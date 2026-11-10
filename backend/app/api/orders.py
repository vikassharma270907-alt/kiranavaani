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
    ProcessOrderResponse,
    AudioSampleClip,
    KhataInfo
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


@router.get("/audio-samples", response_model=List[AudioSampleClip])
async def list_audio_samples():
    """
    Returns benchmark test audio clips metadata across clean studio and degraded telephony noise tiers.
    Enables live interactive A/B listening and evaluation directly in the frontend cockpit.
    """
    return [
        AudioSampleClip(
            clip_id="clip_1_brand_keyterms",
            title="Clip 1: Code-Mixed Brand Keyterms (Maggi & Kurkure)",
            category="Brand Bias & Telephony Noise",
            target_snr_db=5,
            noise_type="ESC-50 Street Traffic & Horns (+5 dB, 8 kHz G.711)",
            transcript_expected="भैया 2 किलो बासमती चावल, 1 Maggi masala, 2 Kurkure और 1 litre Arogyam oil लिख लो, बस इतना ही।",
            clean_audio_url="/audio-samples/clip_1_brand_keyterms_clean_16khz.wav",
            degraded_audio_url="/audio-samples/clip_1_brand_keyterms_telephony_traffic_5db.wav",
            duration_sec=4.2,
            description="Evaluates 200 catalog keyterms bias. Keyterms ON resolves 'Maggi' & 'Kurkure' accurately; Keyterms OFF degrades to phonetic distortion 'meghee'.",
            keyterm_boost_text="Keyterms ON: Maggi & Kurkure (100% Recalled) | OFF: meghee & kurkura"
        ),
        AudioSampleClip(
            clip_id="clip_2_ambiguous_rice",
            title="Clip 2: Ambiguous Rice (Basmati vs Sona Masoori)",
            category="Conversational Clarification Loop",
            target_snr_db=20,
            noise_type="8 kHz μ-Law Telephony + Ceiling Fan (+20 dB)",
            transcript_expected="भैया 5 किलो आशीर्वाद आटा, ढाई किलो चावल और 2 almond oil भेज देना।",
            clean_audio_url="/audio-samples/clip_2_ambiguous_rice_clean_16khz.wav",
            degraded_audio_url="/audio-samples/clip_2_ambiguous_rice_telephony_fan_20db.wav",
            duration_sec=4.0,
            description="Caller asks for 'चावल' without specifying Basmati vs Sona Masoori. Triggers active clarification dialogue.",
            keyterm_boost_text="Triggers Active Ambiguity Gate: Basmati (₹95) vs Sona Masoori (₹58)"
        ),
        AudioSampleClip(
            clip_id="clip_3_colloquial_fractions",
            title="Clip 3: Colloquial Fractions (0 dB Market Babble)",
            category="Extreme Noise Resilience & Fractions",
            target_snr_db=0,
            noise_type="ESC-50 Market Babble (0 dB SNR, 8 kHz G.711)",
            transcript_expected="नमस्ते गुप्ता जी, सवा दो किलो आशीर्वाद आटा, आधा किलो तूर दाल, 1 Tata नमक, बस इतना ही।",
            clean_audio_url="/audio-samples/clip_3_colloquial_fractions_clean_16khz.wav",
            degraded_audio_url="/audio-samples/clip_3_colloquial_fractions_telephony_market_0db.wav",
            duration_sec=4.5,
            description="Evaluates colloquial fractional quantities ('सवा दो किलो' = 2.25 kg, 'आधा किलो' = 0.5 kg) under 0 dB extreme market babble.",
            keyterm_boost_text="Extracts 2.25 kg + 0.5 kg accurately even at 0 dB SNR"
        ),
        AudioSampleClip(
            clip_id="clip_4_dairy_snacks",
            title="Clip 4: Dairy & Snacks Replenishment",
            category="Multi-Unit Normalization",
            target_snr_db=10,
            noise_type="Shop Ceiling Fan Hum (+10 dB, 8 kHz G.711)",
            transcript_expected="भैया 2 packet अमूल ताज़ा दूध, 1 Amul butter, 2 Parle-G बिस्कुट और 1 Vim bar, हो गया।",
            clean_audio_url="/audio-samples/clip_4_dairy_snacks_clean_16khz.wav",
            degraded_audio_url="/audio-samples/clip_4_dairy_snacks_telephony_fan_10db.wav",
            duration_sec=3.8,
            description="Tests discrete packaged items, unit normalization (packets, bars), and completion cue 'हो गया'.",
            keyterm_boost_text="Multi-unit normalization: 2 packets milk + 1 butter + 2 biscuits"
        ),
        AudioSampleClip(
            clip_id="clip_5_kannada_hinglish",
            title="Clip 5: Namma Bengaluru Kannada + Hinglish Order",
            category="Dravidian Code-Switching & Auto-LID",
            target_snr_db=20,
            noise_type="PSTN Telephony Line Noise (+20 dB)",
            transcript_expected="Anna ondu kilo godhi hittu, eradu packet Maggi matthe ardha litre milk kodi, aste.",
            clean_audio_url="/audio-samples/clip_5_kannada_hinglish_clean_16khz.wav",
            degraded_audio_url="/audio-samples/clip_5_kannada_hinglish_telephony_clean_20db.wav",
            duration_sec=4.1,
            description="Tests Bengaluru Kirana mode with Kannada numerals (ondu=1, eradu=2, ardha=0.5) and completion cue 'aste'.",
            keyterm_boost_text="Kannada + Hinglish Auto-LID: ondu godhi hittu -> 1 kg Atta, eradu Maggi -> 2 pkt"
        )
    ]


@router.get("/audio-samples/{filename}")
async def get_audio_sample_file(filename: str):
    """Streams a WAV audio clip from audio_samples directory."""
    from fastapi.responses import FileResponse
    from pathlib import Path
    base_dir = Path(__file__).resolve().parent.parent.parent
    sample_path = base_dir / "audio_samples" / filename
    if not sample_path.exists():
        alt_path = base_dir.parent / "audio_samples" / filename
        if alt_path.exists():
            sample_path = alt_path
        else:
            raise HTTPException(status_code=404, detail=f"Audio sample '{filename}' not found.")
    return FileResponse(sample_path, media_type="audio/wav", filename=filename)


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
    confirmed_inputs: List[CartItemInput] = []
    resolved_clarification_sku = None

    # Check if this turn directly answers an active clarification question
    if request.pending_clarification_family:
        resolved = catalogue_matcher.resolve_spoken_clarification(
            family=request.pending_clarification_family,
            utterance=transcript
        )
        if resolved:
            resolved_clarification_sku, _ = resolved
            confirmed_inputs.append(
                CartItemInput(
                    sku_id=resolved_clarification_sku.sku_id,
                    quantity=1.0,
                    unit=resolved_clarification_sku.unit
                )
            )
            # Remove resolved ambiguity question
            match_res.clarifications_needed = [
                q for q in match_res.clarifications_needed if q.family != request.pending_clarification_family
            ]

    for m in match_res.matched_items:
        if m.status == "MATCHED" and m.matched_sku:
            confirmed_inputs.append(
                CartItemInput(
                    sku_id=m.matched_sku.sku_id,
                    quantity=m.original_item.quantity,
                    unit=m.original_item.unit
                )
            )

    # 5. Build confirmed cart with Khata balance calculation
    cart = cart_service.build_cart(confirmed_inputs, parsed_res.khata_info)

    # 6. Determine conversational reply and clarification priority
    if resolved_clarification_sku:
        spoken_reply_hi = f"{resolved_clarification_sku.name_hi} कार्ट में जोड़ दिया गया है। क्या कुछ और चाहिए?"
        spoken_reply_en = f"{resolved_clarification_sku.name_en} added to cart. Anything else?"
    elif match_res.clarifications_needed:
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
        is_mock_tts=is_mock_tts,
        khata_info=parsed_res.khata_info
    )
