"""
Order processing endpoints for KiranaVaani.
Implements:
- GET /catalogue
- POST /transcribe
- POST /parse-order
- POST /match-products
- POST /cart
- POST /synthesize
- POST /process-order
"""
import base64
import logging
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body
from pydantic import BaseModel

from backend.app.schemas import (
    CatalogueResponse,
    TranscriptionResponse,
    ParseOrderRequest,
    ParseOrderResponse,
    MatchProductsRequest,
    MatchProductsResponse,
    CartRequest,
    CartResponse,
    CartItemInput,
    SynthesizeRequest,
    SynthesizeResponse,
    ProcessOrderRequest,
    ProcessOrderResponse
)
from backend.app.services.prisma_service import prisma_service
from backend.app.services.timbre_service import timbre_service
from backend.app.services.order_parser import order_parser
from backend.app.services.catalogue_matcher import catalogue_matcher
from backend.app.services.cart_service import cart_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Orders & Voice"])


@router.get("/catalogue", response_model=CatalogueResponse)
async def get_catalogue():
    """Returns the Kirana store grocery catalogue (35 SKUs)."""
    skus = catalogue_matcher.get_all_skus()
    return CatalogueResponse(
        store_name=catalogue_matcher.store_name,
        total_skus=len(skus),
        skus=skus
    )


class TranscribeJsonInput(BaseModel):
    audio_base64: str
    keyterms_enabled: bool = True
    language_code: str = "indic-auto"


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: Optional[UploadFile] = File(None),
    body: Optional[TranscribeJsonInput] = Body(None)
):
    """
    Accepts audio input (either as multipart file upload or JSON with base64 audio).
    Calls Gnani AI Prisma REST API. If credentials are not configured, returns mock transcription.
    """
    audio_bytes: Optional[bytes] = None
    filename: str = "audio.wav"
    keyterms_enabled: bool = True

    if file is not None:
        audio_bytes = await file.read()
        filename = file.filename or "audio.wav"
    elif body is not None and body.audio_base64:
        try:
            audio_bytes = base64.b64decode(body.audio_base64)
            keyterms_enabled = body.keyterms_enabled
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 audio payload: {str(e)}")
    else:
        # Default mock mode request
        audio_bytes = b""

    # Extract catalogue keyterms for beam search biasing
    keyterms: List[str] = []
    if keyterms_enabled:
        for sku in catalogue_matcher.get_all_skus():
            keyterms.append(sku.name_hi)
            keyterms.append(sku.name_en)
            keyterms.extend(sku.aliases)

    res = await prisma_service.transcribe_audio(
        audio_bytes=audio_bytes or b"",
        filename=filename,
        keyterms=keyterms
    )
    return res


@router.post("/parse-order", response_model=ParseOrderResponse)
async def parse_order(request: ParseOrderRequest):
    """
    Parses a speech transcript to extract product clauses, normalized quantities, and units.
    Handles Hindi fractional numbers ('aadha' -> 0.5, 'dhai' -> 2.5, 'sawa' -> 1.25).
    """
    return order_parser.parse_utterance(
        text=request.transcript,
        keyterms_enabled=request.keyterms_enabled
    )


@router.post("/match-products", response_model=MatchProductsResponse)
async def match_products(request: MatchProductsRequest):
    """
    Matches extracted items against the catalogue.
    Flags ambiguous products (e.g. 'chawal' without specifying Basmati vs Sona Masoori)
    and low-confidence mentions to trigger clarification questions.
    """
    return catalogue_matcher.match_items(
        items=request.items,
        keyterms_enabled=request.keyterms_enabled
    )


@router.post("/cart", response_model=CartResponse)
async def create_cart(request: CartRequest):
    """
    Creates a structured cart from confirmed product SKUs and quantities.
    Calculates subtotals, totals, and generates spoken confirmation text.
    """
    return cart_service.build_cart(request.items)


@router.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize_voice(request: SynthesizeRequest):
    """
    Converts order confirmation or clarification text into natural speech via Gnani AI Timbre.
    If API credentials are not configured, returns playable fallback audio.
    """
    return await timbre_service.synthesize_speech(
        text=request.text,
        voice=request.voice,
        language=request.language,
        speed=request.speed
    )


@router.post("/process-order", response_model=ProcessOrderResponse)
async def process_order(request: ProcessOrderRequest):
    """
    Combined end-to-end pipeline:
    1. Transcribe audio if provided, or use input transcript text.
    2. Parse products, quantities, and units with numeral normalization.
    3. Match against catalogue and detect ambiguities.
    4. If ambiguities or low confidence exist, PRESERVE them for customer clarification.
    5. Build cart with confirmed high-confidence items.
    6. Generate spoken summary and optionally synthesize confirmation audio.
    """
    # 1. Obtain transcript
    transcript = ""
    is_mock_asr = False
    if request.audio_base64:
        try:
            audio_bytes = base64.b64decode(request.audio_base64)
            asr_res = await prisma_service.transcribe_audio(audio_bytes=audio_bytes)
            transcript = asr_res.transcript
            is_mock_asr = asr_res.is_mock
        except Exception as e:
            logger.error(f"Failed to transcribe audio in process-order: {e}")
            transcript = request.transcript or "Bhaiya do packet Maggi, ek kilo sugar aur aadha litre milk bhej dena."
            is_mock_asr = True
    elif request.transcript:
        transcript = request.transcript
    else:
        transcript = "Bhaiya do packet Maggi, ek kilo sugar aur aadha litre milk bhej dena."
        is_mock_asr = True

    # 2. Parse utterance
    parsed_res = order_parser.parse_utterance(
        text=transcript,
        keyterms_enabled=request.keyterms_enabled
    )

    # 3. Match against catalogue
    match_res = catalogue_matcher.match_items(
        items=parsed_res.items,
        keyterms_enabled=request.keyterms_enabled
    )

    # 4. Filter confirmed items vs ambiguous items
    # CRITICAL: We DO NOT automatically convert ambiguous items into confirmed orders!
    confirmed_inputs: List[CartItemInput] = []
    for m in match_res.matched_items:
        if m.status == "MATCHED" and m.matched_sku:
            confirmed_inputs.append(
                CartItemInput(
                    sku_id=m.matched_sku.sku_id,
                    quantity=m.original_item.quantity,
                    unit=m.original_item.unit
                )
            )

    # 5. Build confirmed cart
    cart = cart_service.build_cart(confirmed_inputs)

    # 6. Determine conversational reply and clarification priority
    if match_res.clarifications_needed:
        # Prioritize asking the first ambiguous question
        top_clarification = match_res.clarifications_needed[0]
        spoken_reply_hi = top_clarification.question_hi
        spoken_reply_en = top_clarification.question_en
    elif cart.items:
        spoken_reply_hi = cart.spoken_summary_hi
        spoken_reply_en = cart.spoken_summary_en
    else:
        spoken_reply_hi = "क्षमा करें, कोई किराना सामान पहचाना नहीं जा सका। कृपया दोबारा बोलें।"
        spoken_reply_en = "Sorry, no grocery items were recognized. Please repeat your order."

    # 7. Synthesize audio if requested
    voice_audio_b64 = None
    voice_audio_fmt = None
    is_mock_tts = False
    if request.synthesize_voice:
        synth_res = await timbre_service.synthesize_speech(
            text=spoken_reply_hi,
            voice="Nalini",
            language="hi-IN"
        )
        voice_audio_b64 = synth_res.audio_base64
        voice_audio_fmt = synth_res.audio_format
        is_mock_tts = synth_res.is_mock

    return ProcessOrderResponse(
        transcript=transcript,
        normalized_transcript=parsed_res.normalized_transcript,
        is_mock_asr=is_mock_asr,
        parsed_items=parsed_res.items,
        is_order_complete=parsed_res.is_order_complete,
        confirmed_cart=cart,
        clarifications_needed=match_res.clarifications_needed,
        unmatched_items=match_res.unmatched_items,
        spoken_reply_hi=spoken_reply_hi,
        spoken_reply_en=spoken_reply_en,
        voice_audio_base64=voice_audio_b64,
        voice_audio_format=voice_audio_fmt,
        is_mock_tts=is_mock_tts
    )
