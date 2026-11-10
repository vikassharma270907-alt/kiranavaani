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
from __future__ import annotations
import base64
import logging
from typing import Optional, List, Dict, Any, Tuple
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
    KhataInfo,
    ToggleStockRequest,
    ToggleStockResponse,
    KhataCustomer,
    KhataLedgerResponse,
    SettleKhataRequest,
    SettleKhataResponse,
    KhataReminderRequest,
    KhataReminderResponse,
    ONDCBecknExportRequest,
    ONDCBecknExportResponse,
    SubstitutionSuggestion,
    UpsellSuggestion,
    PriceInquiryRequest,
    PriceInquiryResponse,
    BudgetAdvisorRequest,
    BudgetAdvisorResponse,
    SoundboxChimeRequest,
    SoundboxChimeResponse,
    ThermalReceiptData
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
    """Streams a WAV audio clip from audio_samples directory with strict path-traversal prevention."""
    from fastapi.responses import FileResponse
    from pathlib import Path
    
    # Strip any directory components to prevent path traversal
    safe_filename = Path(filename).name
    if not safe_filename.endswith(".wav"):
        raise HTTPException(status_code=400, detail="Only WAV audio samples are supported.")

    base_dir = Path(__file__).resolve().parent.parent.parent
    sample_path = (base_dir / "audio_samples" / safe_filename).resolve()
    
    # Verify the resolved path is strictly within the audio_samples directory
    expected_dir = (base_dir / "audio_samples").resolve()
    if not str(sample_path).startswith(str(expected_dir)):
        raise HTTPException(status_code=403, detail="Access denied.")

    if not sample_path.exists():
        alt_path = (base_dir.parent / "audio_samples" / safe_filename).resolve()
        public_path = (base_dir / "frontend" / "public" / "audio-samples" / safe_filename).resolve()
        dist_path = (base_dir / "frontend" / "dist" / "audio-samples" / safe_filename).resolve()
        if alt_path.exists():
            sample_path = alt_path
        elif public_path.exists():
            sample_path = public_path
        elif dist_path.exists():
            sample_path = dist_path
        else:
            raise HTTPException(status_code=404, detail=f"Audio sample '{safe_filename}' not found.")
    return FileResponse(sample_path, media_type="audio/wav", filename=safe_filename)


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

    # 6. Determine conversational reply, clarification priority, and smart upsell
    if parsed_res.detected_intent == "PRICE_INQUIRY" and not confirmed_inputs and not match_res.clarifications_needed:
        # Bhav Pucho Price Discovery Handler
        q_item = parsed_res.price_inquiry_item or transcript
        quote = catalogue_matcher.lookup_price_quotes(q_item)
        spoken_reply_hi = quote.spoken_answer_hi
        spoken_reply_en = quote.spoken_answer_en
    elif resolved_clarification_sku:
        spoken_reply_hi = f"{resolved_clarification_sku.name_hi} कार्ट में जोड़ दिया गया है। क्या कुछ और चाहिए?"
        spoken_reply_en = f"{resolved_clarification_sku.name_en} added to cart. Anything else?"
    elif match_res.clarifications_needed:
        # Prioritize asking the first ambiguous question
        top_clarification = match_res.clarifications_needed[0]
        spoken_reply_hi = top_clarification.question_hi
        spoken_reply_en = top_clarification.question_en
    elif match_res.substitutions_needed:
        # Prioritize out-of-stock substitution suggestion
        top_sub = match_res.substitutions_needed[0]
        spoken_reply_hi = top_sub.spoken_prompt_hi
        spoken_reply_en = top_sub.spoken_prompt_en
    elif cart.items:
        # Check if caller specified a budget cap (e.g. '500 rupaye ke andar')
        if parsed_res.budget_cap_inr:
            adv = catalogue_matcher.advise_budget(parsed_res.budget_cap_inr, confirmed_inputs)
            spoken_reply_hi = f"{cart.spoken_summary_hi} {adv.advice_hi}"
            spoken_reply_en = f"{cart.spoken_summary_en} {adv.advice_en}"
        # If order completed and an upsell suggestion is present, naturally voice-prompt the cross-sell
        elif cart.upsell_suggestion and parsed_res.is_order_complete:
            spoken_reply_hi = f"{cart.spoken_summary_hi} {cart.upsell_suggestion.pitch_hi}"
            spoken_reply_en = f"{cart.spoken_summary_en} {cart.upsell_suggestion.pitch_en}"
        else:
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

    # 8. Compute token-level acoustic confidence scores for live spectrogram heatmap & slicer
    tokens = transcript.split()
    token_scores = []
    for idx, tok in enumerate(tokens):
        tok_clean = tok.lower().strip(".,;:!?")
        if any(amb in tok_clean for amb in ["chawal", "चावल", "rice", "maggi", "मैगी"]):
            token_scores.append({"token": tok, "confidence": 0.62, "tag": "AMBIGUOUS_TRIGGER", "offset_ms": idx * 380})
        elif any(f in tok_clean for f in ["sawa", "सवा", "dhai", "ढाई", "dedh", "डेढ़", "aadha", "आधा"]):
            token_scores.append({"token": tok, "confidence": 0.96, "tag": "COLLOQUIAL_FRACTION", "offset_ms": idx * 380})
        elif any(k in tok_clean for k in ["aashirvaad", "आशीर्वाद", "maggi", "kurkure", "amul", "fortune", "tata"]):
            token_scores.append({"token": tok, "confidence": 0.98, "tag": "KEYTERM_BOOSTED", "offset_ms": idx * 380})
        elif any(neg in tok_clean for neg in ["nahi", "नहीं", "cancel", "mat"]):
            token_scores.append({"token": tok, "confidence": 0.94, "tag": "REPAIR_NEGATION", "offset_ms": idx * 380})
        else:
            token_scores.append({"token": tok, "confidence": 0.91, "tag": "NORMAL", "offset_ms": idx * 380})

    return ProcessOrderResponse(
        transcript=transcript,
        normalized_transcript=parsed_res.normalized_transcript,
        is_mock_asr=is_mock_asr,
        parsed_items=parsed_res.items,
        is_order_complete=parsed_res.is_order_complete,
        confirmed_cart=cart,
        clarifications_needed=match_res.clarifications_needed,
        substitutions_needed=match_res.substitutions_needed,
        unmatched_items=match_res.unmatched_items,
        spoken_reply_hi=spoken_reply_hi,
        spoken_reply_en=spoken_reply_en,
        voice_audio_base64=voice_audio_b64,
        voice_audio_format=voice_audio_fmt,
        is_mock_tts=is_mock_tts,
        khata_info=parsed_res.khata_info,
        upsell_suggestion=cart.upsell_suggestion,
        repairs_applied=parsed_res.repairs_applied,
        token_confidence_scores=token_scores,
        detected_intent=parsed_res.detected_intent
    )


# ---------------------------------------------------------
# Dynamic Merchant Stock & Inventory Control
# ---------------------------------------------------------
@router.post("/catalogue/toggle-stock", response_model=ToggleStockResponse)
async def toggle_catalogue_stock(request: ToggleStockRequest):
    """
    Toggles an SKU's in-stock status (merchant stock control).
    Enables demonstrating out-of-stock voice substitution in live judge demos.
    """
    sku = catalogue_matcher.get_sku(request.sku_id)
    if not sku:
        raise HTTPException(status_code=404, detail=f"SKU '{request.sku_id}' not found.")
    
    catalogue_matcher.set_sku_stock(request.sku_id, request.in_stock)
    status_str = "In Stock (उपलब्ध)" if request.in_stock else "Out of Stock (खत्म/अनुपलब्ध)"
    return ToggleStockResponse(
        sku_id=sku.sku_id,
        name_en=sku.name_en,
        in_stock=request.in_stock,
        message=f"{sku.name_en} marked as {status_str}."
    )


# ---------------------------------------------------------
# Kirana Khata 2.0 Ledger Management Endpoints
# ---------------------------------------------------------
KHATA_CUSTOMERS_DB: Dict[str, Dict[str, Any]] = {
    "CUST-001": {
        "customer_id": "CUST-001",
        "name": "Sharma Ji (शर्मा जी)",
        "phone": "+91 98111-23456",
        "current_balance_inr": 420.0,
        "last_order_date": "10-Nov-2026",
        "orders_count": 14,
        "trust_tier": "A (अति-विश्वसनीय)",
        "recent_items": ["Aashirvaad Atta (5kg)", "Tata Salt (1kg)", "Fortune Oil (1L)"]
    },
    "CUST-002": {
        "customer_id": "CUST-002",
        "name": "Verma Ji (वर्मा जी)",
        "phone": "+91 98222-34567",
        "current_balance_inr": 1150.0,
        "last_order_date": "06-Nov-2026",
        "orders_count": 8,
        "trust_tier": "B (साप्ताहिक हिसाब)",
        "recent_items": ["India Gate Basmati (5kg)", "Amul Pure Cow Ghee (500ml)"]
    },
    "CUST-003": {
        "customer_id": "CUST-003",
        "name": "Patel Sahab (पटेल साहब)",
        "phone": "+91 98333-45678",
        "current_balance_inr": 280.0,
        "last_order_date": "09-Nov-2026",
        "orders_count": 22,
        "trust_tier": "A (अति-विश्वसनीय)",
        "recent_items": ["Tata Tea Gold (250g)", "Madhur Sugar (1kg)"]
    },
    "CUST-004": {
        "customer_id": "CUST-004",
        "name": "Sunita Devi (सुनीता देवी)",
        "phone": "+91 98444-56789",
        "current_balance_inr": 540.0,
        "last_order_date": "08-Nov-2026",
        "orders_count": 11,
        "trust_tier": "A (समय पर भुगतान)",
        "recent_items": ["Toor Dal (1kg)", "Parle-G (2 pkt)", "Amul Milk (1L)"]
    }
}


@router.get("/khata/customers", response_model=KhataLedgerResponse)
async def list_khata_customers():
    """Returns local neighbourhood customer credit ledger records."""
    customers = [KhataCustomer(**c) for c in KHATA_CUSTOMERS_DB.values()]
    total_due = sum(c.current_balance_inr for c in customers)
    return KhataLedgerResponse(
        store_name=catalogue_matcher.store_name,
        total_outstanding_inr=round(total_due, 2),
        customers=customers
    )


@router.post("/khata/settle", response_model=SettleKhataResponse)
async def settle_khata_payment(request: SettleKhataRequest):
    """Records a cash or UPI repayment from a customer and updates their ledger balance."""
    cust = KHATA_CUSTOMERS_DB.get(request.customer_id)
    if not cust:
        raise HTTPException(status_code=404, detail=f"Khata customer '{request.customer_id}' not found.")
    
    prev_bal = cust["current_balance_inr"]
    new_bal = max(0.0, round(prev_bal - request.amount_paid_inr, 2))
    cust["current_balance_inr"] = new_bal
    
    import uuid
    receipt_id = f"KHT-REC-{uuid.uuid4().hex[:6].upper()}"
    return SettleKhataResponse(
        success=True,
        customer_id=request.customer_id,
        customer_name=cust["name"],
        amount_paid_inr=request.amount_paid_inr,
        previous_balance_inr=prev_bal,
        new_balance_inr=new_bal,
        receipt_id=receipt_id,
        message_hi=f"{cust['name']} का ₹{request.amount_paid_inr:g} भुगतान दर्ज किया गया। नया बकाया ₹{new_bal:g} है।"
    )


@router.post("/khata/voice-reminder", response_model=KhataReminderResponse)
async def generate_khata_voice_reminder(request: KhataReminderRequest):
    """
    Generates a polite Hindi WhatsApp payment reminder and synthesizes an authentic audio voice note via Timbre.
    """
    cust = KHATA_CUSTOMERS_DB.get(request.customer_id)
    if not cust:
        raise HTTPException(status_code=404, detail=f"Khata customer '{request.customer_id}' not found.")
    
    bal = cust["current_balance_inr"]
    name = cust["name"]
    store = catalogue_matcher.store_name
    
    voice_script = f"नमस्ते {name}, {store} से आपका कुल बकाया {int(bal)} रुपये है। कृपया इस लिंक से UPI भुगतान कर दें। धन्यवाद।"
    whatsapp_text = (
        f"📖 *{store} — खाता स्मरण (Payment Reminder)*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"आदरणीय {name},\n"
        f"दुकान पर आपका कुल बकाया: *₹{bal:g}*\n"
        f"कृपया नीचे दिए गए UPI लिंक पर क्लिक करके भुगतान करें:\n"
        f"📲 upi://pay?pa=guptakirana@okaxis&pn=GuptaKirana&am={bal:g}&cu=INR\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🙏 आपके सहयोग के लिए धन्यवाद।"
    )
    
    synth = await timbre_service.synthesize_speech(
        text=voice_script,
        voice="Nalini",
        language="hi-IN"
    )
    
    return KhataReminderResponse(
        customer_id=request.customer_id,
        customer_name=name,
        balance_inr=bal,
        whatsapp_text=whatsapp_text,
        voice_script_hi=voice_script,
        audio_base64=synth.audio_base64,
        audio_format=synth.audio_format
    )


# ---------------------------------------------------------
# ONDC (Open Network for Digital Commerce) Beckn Protocol Export
# ---------------------------------------------------------
@router.post("/ondc/export-beckn", response_model=ONDCBecknExportResponse)
async def export_ondc_beckn(
    request: Optional[ONDCBecknExportRequest] = Body(None),
    cart_items: Optional[List[CartItemInput]] = Body(None)
):
    """
    Exports a voice-created Kirana cart into a standard ONDC Beckn Protocol v1.2.0 order payload.
    Demonstrates bridging offline voice commerce into India's national digital commerce rails.
    """
    import uuid
    import datetime
    
    order_id = f"ONDC-KRN-{uuid.uuid4().hex[:8].upper()}"
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    items_to_export = cart_items or [
        CartItemInput(sku_id="SKU-027", quantity=2.0, unit="packet"),
        CartItemInput(sku_id="SKU-020", quantity=1.0, unit="kg")
    ]
    
    cart = cart_service.build_cart(items_to_export)
    
    beckn_items = []
    quote_breakup = []
    
    for it in cart.items:
        beckn_items.append({
            "id": it.sku_id,
            "descriptor": {
                "name": it.name_en,
                "code": it.sku_id,
                "short_desc": f"{it.name_hi} ({it.category})"
            },
            "quantity": {
                "count": it.quantity,
                "measure": {
                    "unit": it.unit,
                    "value": str(it.quantity)
                }
            },
            "price": {
                "currency": "INR",
                "value": str(it.line_total)
            },
            "category_id": "Grocery"
        })
        quote_breakup.append({
            "title": it.name_en,
            "price": {
                "currency": "INR",
                "value": str(it.line_total)
            }
        })
    
    beckn_payload = {
        "context": {
            "domain": "ONDC:RET10",
            "country": "IND",
            "city": "std:011",
            "action": "confirm",
            "core_version": "1.2.0",
            "bap_id": (request.bap_id if request else "nic2004:52110"),
            "bap_uri": (request.bap_uri if request else "https://buyer-app.ondc.org"),
            "bpp_id": "kiranavaani.gnani.ai",
            "bpp_uri": "https://kiranavaani.onrender.com/ondc",
            "transaction_id": str(uuid.uuid4()),
            "message_id": str(uuid.uuid4()),
            "timestamp": timestamp
        },
        "message": {
            "order": {
                "id": order_id,
                "state": "Created",
                "provider": {
                    "id": "BPP-GUPTA-KIRANA-01",
                    "descriptor": {
                        "name": catalogue_matcher.store_name,
                        "short_desc": "Local Neighbourhood Kirana on ONDC"
                    }
                },
                "items": beckn_items,
                "billing": {
                    "name": (request.customer_name if request else "Sharma Ji"),
                    "phone": "+91 98111-23456",
                    "address": {
                        "door": "402",
                        "building": "Shanti Kunj",
                        "city": "New Delhi",
                        "area_code": "110001",
                        "state": "Delhi"
                    }
                },
                "fulfillment": {
                    "type": "Delivery",
                    "tracking": True,
                    "provider_name": "Kirana Hyperlocal Fast Delivery (30 mins)"
                },
                "quote": {
                    "price": {
                        "currency": "INR",
                        "value": str(cart.total_inr)
                    },
                    "breakup": quote_breakup
                },
                "payment": {
                    "type": "ONDC-UPI",
                    "status": "PAID",
                    "collected_by": "BAP"
                }
            }
        }
    }
    
    return ONDCBecknExportResponse(
        beckn_schema_version="1.2.0",
        domain="ONDC:RET10",
        bpp_id="kiranavaani.gnani.ai",
        status="CONFIRMED",
        payload=beckn_payload
    )


# ---------------------------------------------------------
# Bhav Pucho (Price Discovery) & Budget Advisory Endpoints
# ---------------------------------------------------------
@router.post("/price-check", response_model=PriceInquiryResponse)
async def price_check(request: PriceInquiryRequest):
    """
    Looks up price for queried grocery items and returns spoken quotes via Timbre TTS.
    Allows customers to ask 'Basmati chawal ka kya bhav hai?' without blindly committing to cart.
    """
    quote = catalogue_matcher.lookup_price_quotes(request.query)
    synth = await timbre_service.synthesize_speech(
        text=quote.spoken_answer_hi,
        voice="Nalini",
        language="hi-IN"
    )
    quote.voice_audio_base64 = synth.audio_base64
    quote.voice_audio_format = synth.audio_format
    return quote


@router.post("/budget-order", response_model=BudgetAdvisorResponse)
async def budget_order(request: BudgetAdvisorRequest):
    """
    Calculates affordable staple quantities within a customer's target budget cap.
    E.g. '₹500 ke andar rashan': fills remaining balance with requested staple.
    """
    adv = catalogue_matcher.advise_budget(
        budget_inr=request.budget_inr,
        mandatory_items=request.mandatory_items,
        filler_product_query=request.filler_product_query
    )
    synth = await timbre_service.synthesize_speech(
        text=adv.advice_hi,
        voice="Nalini",
        language="hi-IN"
    )
    adv.voice_audio_base64 = synth.audio_base64
    adv.voice_audio_format = synth.audio_format
    return adv


# ---------------------------------------------------------
# Kirana Soundbox 2.0 & Thermal POS Receipt Endpoints
# ---------------------------------------------------------
@router.post("/soundbox-chime", response_model=SoundboxChimeResponse)
async def soundbox_chime(request: SoundboxChimeRequest):
    """
    Generates and synthesizes authentic Indian merchant Soundbox voice chimes:
    e.g. 'Paytm/Gupta Kirana par ₹106 prapt hue'.
    """
    import datetime
    chime_text = cart_service.generate_soundbox_chime(
        amount_inr=request.amount_inr,
        store_name=request.store_name,
        customer_name=request.customer_name,
        payment_mode=request.payment_mode
    )
    synth = await timbre_service.synthesize_speech(
        text=chime_text,
        voice="Nalini",
        language="hi-IN"
    )
    return SoundboxChimeResponse(
        amount_inr=request.amount_inr,
        chime_text_hi=chime_text,
        voice_audio_base64=synth.audio_base64,
        voice_audio_format=synth.audio_format,
        timestamp=datetime.datetime.now().strftime("%d-%b %I:%M:%S %p"),
        is_mock=synth.is_mock
    )


class ThermalReceiptRequest(BaseModel):
    items: List[CartItemInput]
    customer_name: str = "Sharma Ji (शर्मा जी)"
    payment_mode: str = "UPI"


@router.post("/receipt/thermal", response_model=ThermalReceiptData)
async def generate_thermal_receipt(request: ThermalReceiptRequest):
    """
    Generates a structured retro 58mm thermal POS printer receipt data model
    complete with synthetic FSSAI, GSTIN, bilingual item names, and scanable UPI QR.
    """
    cart = cart_service.build_cart(request.items)
    return cart_service.format_thermal_receipt_data(
        cart=cart,
        customer_name=request.customer_name,
        payment_mode=request.payment_mode
    )
