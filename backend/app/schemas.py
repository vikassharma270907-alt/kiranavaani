"""
Pydantic data models for KiranaVaani API requests and responses.
"""
from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, computed_field


# ---------------------------------------------------------
# Health Check Schemas
# ---------------------------------------------------------
class HealthResponse(BaseModel):
    status: str = Field(..., examples=["healthy"])
    version: str = Field(..., examples=["2.0.0"])
    service: str = Field("KiranaVaani Backend", examples=["KiranaVaani Backend"])
    gnani_live_configured: bool = Field(False, description="True if a valid Gnani API key is configured")
    live_api_configured: bool = Field(False, description="True if GNANI_API_KEY starts with vach_")
    gnani_stt_model: str = Field("prisma-v3.0")
    gnani_tts_model: str = Field("timbre-v2.5")
    catalogue_sku_count: int = Field(35)
    supported_languages: List[str] = Field(default_factory=lambda: ["hi-IN", "en-IN", "Hinglish"])


# ---------------------------------------------------------
# Catalogue Schemas
# ---------------------------------------------------------
class CatalogueSKU(BaseModel):
    sku_id: str = Field(..., examples=["SKU-001"])
    name_en: str = Field(..., examples=["Aashirvaad Chakki Atta"])
    name_hi: str = Field(..., examples=["आशीर्वाद चक्की आटा"])
    name_kn: Optional[str] = None
    name_ta: Optional[str] = None
    category: str = Field(..., examples=["Flour & Grains"])
    unit: str = Field(..., examples=["kg"])
    price_inr: float = Field(..., examples=[52.0])
    aliases: List[str] = Field(default_factory=list)
    ambiguous_family: Optional[str] = None
    in_stock: bool = Field(True, description="Stock availability status")
    substitutes: List[str] = Field(default_factory=list, description="SKU IDs of recommended substitutes if out of stock")


class CatalogueResponse(BaseModel):
    store_name: str = Field("Gupta Kirana & General Store")
    total_skus: int
    skus: List[CatalogueSKU]


# ---------------------------------------------------------
# Transcription Schemas
# ---------------------------------------------------------
class TranscriptionResponse(BaseModel):
    transcript: str = Field(..., examples=["Bhaiya do packet Maggi, ek kilo sugar aur aadha litre milk bhej dena."])
    language_detected: str = Field("hi-Latn / hi-Deva (Code-Mixed)", examples=["Hinglish"])
    confidence: float = Field(0.95, ge=0.0, le=1.0)
    model: str = Field("prisma-v3.0")
    is_mock: bool = Field(False, description="True if generated via fallback mock mode")
    duration_sec: Optional[float] = None
    note: Optional[str] = None


# ---------------------------------------------------------
# Order Parsing & Khata Schemas
# ---------------------------------------------------------
class KhataInfo(BaseModel):
    is_khata: bool = Field(False, description="True if order was requested on store credit (udhaar/khata)")
    customer_id: Optional[str] = Field("CUST-001", description="Associated customer ID in Khata Ledger")
    customer_name: Optional[str] = Field(None, description="Extracted customer name e.g. 'Sharma Ji'")
    khata_id: Optional[str] = Field(None, description="Account ID e.g. '#42'")
    previous_balance_inr: float = Field(420.0, description="Previous ledger balance")
    current_order_inr: float = Field(0.0, description="Current order total")
    new_balance_inr: float = Field(0.0, description="Total outstanding balance including this order")
    payment_mode: str = Field("cash", description="'khata', 'upi', or 'cash'")
    note_hi: Optional[str] = None


class ParsedItem(BaseModel):
    product: str = Field(..., examples=["Maggi"])
    quantity: float = Field(..., examples=[2.0])
    unit: str = Field(..., examples=["packet"])
    raw_clause: Optional[str] = None


class RepairedItemEvent(BaseModel):
    original_phrase: str
    action: str = Field(..., description="'CORRECTED_QUANTITY' or 'CANCELLED_ITEM'")
    product: str
    previous_quantity: Optional[float] = None
    new_quantity: Optional[float] = None
    explanation: str


class ParseOrderRequest(BaseModel):
    transcript: str = Field(..., max_length=1000, examples=["Bhaiya do packet Maggi, ek kilo sugar aur aadha litre milk bhej dena."])
    keyterms_enabled: bool = Field(True, description="Enable catalogue keyterms biasing")


class ParseOrderResponse(BaseModel):
    raw_transcript: str
    normalized_transcript: str
    items: List[ParsedItem]
    is_order_complete: bool = Field(False, description="True if caller expressed completion e.g. 'bas itna hi'")
    khata_info: Optional[KhataInfo] = None
    repairs_applied: List[RepairedItemEvent] = Field(default_factory=list)
    detected_intent: str = Field("ORDER", description="'ORDER', 'PRICE_INQUIRY', or 'BUDGET_QUERY'")
    price_inquiry_item: Optional[str] = None
    budget_cap_inr: Optional[float] = None


# ---------------------------------------------------------
# Catalogue Matching & Ambiguity Schemas
# ---------------------------------------------------------
class MatchCandidate(BaseModel):
    sku_id: str
    name_en: str
    name_hi: str
    unit: str
    price_inr: float
    score: float
    matched_alias: Optional[str] = None


class ClarificationOption(BaseModel):
    sku_id: str
    name_en: str
    name_hi: str
    category: Optional[str] = "Groceries"
    quantity: float
    unit: str
    price_inr: float


class ClarificationQuestion(BaseModel):
    family: str = Field(..., examples=["rice"])
    spoken_phrase: str = Field(..., examples=["ek kilo chawal"])
    question_hi: str = Field(..., examples=["'इंडिया गेट बासमती चावल' चाहिए या 'साधारण सोना मसूरी'?"])
    question_en: str = Field(..., examples=["India Gate Basmati Rice or Sona Masoori Regular Rice?"])
    options: List[ClarificationOption]
    confidence: float


class SubstitutionSuggestion(BaseModel):
    original_item_name: str
    out_of_stock_sku: CatalogueSKU
    substitute_sku: CatalogueSKU
    reason_hi: str
    reason_en: str
    spoken_prompt_hi: str
    spoken_prompt_en: str


class ProductMatchResult(BaseModel):
    original_item: ParsedItem
    status: str = Field(..., examples=["MATCHED"], description="'MATCHED', 'CLARIFICATION_REQUIRED', 'OUT_OF_STOCK_SUBSTITUTION', or 'UNRECOGNIZED'")
    confidence: float
    matched_sku: Optional[CatalogueSKU] = None
    clarification: Optional[ClarificationQuestion] = None
    substitution: Optional[SubstitutionSuggestion] = None
    candidates: List[MatchCandidate] = Field(default_factory=list)


class MatchProductsRequest(BaseModel):
    items: List[ParsedItem] = Field(..., max_length=100)
    keyterms_enabled: bool = True


class MatchProductsResponse(BaseModel):
    matched_items: List[ProductMatchResult]
    clarifications_needed: List[ClarificationQuestion]
    substitutions_needed: List[SubstitutionSuggestion] = Field(default_factory=list)
    unmatched_items: List[ParsedItem]


# ---------------------------------------------------------
# Shopping Cart Schemas
# ---------------------------------------------------------
class CartItemInput(BaseModel):
    sku_id: str
    quantity: float = Field(..., gt=0.0, le=500.0, description="Quantity must be strictly positive and <= 500")
    unit: Optional[str] = Field(None, max_length=25)


class CartItem(BaseModel):
    sku_id: str
    name_en: str
    name_hi: str
    category: str
    quantity: float
    unit: str
    unit_price: float
    line_total: float


class CartRequest(BaseModel):
    items: List[CartItemInput]


class UpsellSuggestion(BaseModel):
    sku_id: str
    name_en: str
    name_hi: str
    category: str
    price_inr: float
    unit: str
    quantity: float = 1.0
    pitch_hi: str
    pitch_en: str
    reason_tag: str


class CartResponse(BaseModel):
    items: List[CartItem]
    item_count: int
    subtotal_inr: float
    delivery_fee_inr: float = 0.0
    total_inr: float
    spoken_summary_hi: str
    spoken_summary_en: str
    upsell_suggestion: Optional[UpsellSuggestion] = None


# ---------------------------------------------------------
# Voice Synthesis (TTS) Schemas
# ---------------------------------------------------------
class SynthesizeRequest(BaseModel):
    text: str = Field(..., examples=["Aapke order me 2 packet Maggi aur 1 kilo sugar shamil hai. Kul 73 rupaye."])
    voice: str = Field("Nalini")
    model: str = Field("timbre-v2.5")
    language: str = Field("hi-IN")
    speed: float = Field(1.0)


class SynthesizeResponse(BaseModel):
    text: str
    audio_base64: str = Field(..., description="Base64-encoded audio bytes (WAV or MP3)")
    audio_format: str = Field("wav")
    duration_sec: float
    is_mock: bool = Field(False)
    voice: str = "Nalini"
    model: str = "timbre-v2.5"
    note: Optional[str] = None


# ---------------------------------------------------------
# Audio Samples Schema
# ---------------------------------------------------------
class AudioSampleClip(BaseModel):
    clip_id: str
    title: str
    category: str
    target_snr_db: int
    noise_type: str
    transcript_expected: str
    clean_audio_url: str
    degraded_audio_url: str
    duration_sec: float
    description: str
    keyterm_boost_text: str


# ---------------------------------------------------------
# Combined End-to-End Pipeline Schemas
# ---------------------------------------------------------
class ProcessOrderRequest(BaseModel):
    transcript: Optional[str] = Field(None, max_length=1000, description="Raw transcription text")
    audio_base64: Optional[str] = Field(None, max_length=15_000_000, description="Base64 audio payload (max ~10MB)")
    keyterms_enabled: bool = True
    synthesize_voice: bool = True
    pending_clarification_family: Optional[str] = Field(None, description="Active ambiguity family if caller is replying to a clarification")


class ProcessOrderResponse(BaseModel):
    transcript: str
    normalized_transcript: str
    is_mock_asr: bool
    parsed_items: List[ParsedItem]
    is_order_complete: bool
    confirmed_cart: CartResponse
    clarifications_needed: List[ClarificationQuestion]
    substitutions_needed: List[SubstitutionSuggestion] = Field(default_factory=list)
    unmatched_items: List[ParsedItem]
    spoken_reply_hi: str
    spoken_reply_en: str
    voice_audio_base64: Optional[str] = None
    voice_audio_format: Optional[str] = None
    is_mock_tts: bool = False
    khata_info: Optional[KhataInfo] = None
    upsell_suggestion: Optional[UpsellSuggestion] = None
    repairs_applied: List[RepairedItemEvent] = Field(default_factory=list)
    token_confidence_scores: List[Dict[str, Any]] = Field(default_factory=list)
    detected_intent: str = Field("ORDER", description="'ORDER', 'PRICE_INQUIRY', or 'BUDGET_QUERY'")
    landmark_info: Optional["DeliveryLandmarkInfo"] = None
    bhaav_taal_info: Optional["BhaavTaalResponse"] = None
    recipe_info: Optional["RecipeToCartResponse"] = None
    jazbaat_info: Optional["CustomerJazbaatInfo"] = None
    liveness_info: Optional["LivenessCheckResponse"] = None


# ---------------------------------------------------------
# Inventory Stock Management Schemas
# ---------------------------------------------------------
class ToggleStockRequest(BaseModel):
    sku_id: str
    in_stock: bool


class ToggleStockResponse(BaseModel):
    sku_id: str
    name_en: str
    in_stock: bool
    message: str


# ---------------------------------------------------------
# Kirana Khata 2.0 Ledger Schemas
# ---------------------------------------------------------
class KhataCustomer(BaseModel):
    customer_id: str
    name: str
    phone: str
    current_balance_inr: float
    last_order_date: str
    orders_count: int
    trust_tier: str = "A"
    recent_items: List[str] = Field(default_factory=list)


class KhataLedgerResponse(BaseModel):
    store_name: str
    total_outstanding_inr: float
    customers: List[KhataCustomer]


class SettleKhataRequest(BaseModel):
    customer_id: str = Field(..., max_length=20)
    amount_paid_inr: float = Field(..., gt=0.0, le=100000.0, description="Repayment amount must be positive")
    payment_mode: str = Field("cash", max_length=25)


class SettleKhataResponse(BaseModel):
    success: bool
    customer_id: str
    customer_name: str
    amount_paid_inr: float
    previous_balance_inr: float
    new_balance_inr: float
    receipt_id: str
    message_hi: str


class KhataReminderRequest(BaseModel):
    customer_id: str


class KhataReminderResponse(BaseModel):
    customer_id: str
    customer_name: str
    balance_inr: float
    whatsapp_text: str
    voice_script_hi: str
    audio_base64: Optional[str] = None
    audio_format: str = "wav"


# ---------------------------------------------------------
# ONDC Beckn Protocol Export Schemas
# ---------------------------------------------------------
class ONDCBecknExportRequest(BaseModel):
    bap_id: str = "nic2004:52110"
    bap_uri: str = "https://buyer-app.ondc.org"
    customer_name: Optional[str] = "Sharma Ji"
    delivery_address: Optional[str] = "Flat 402, Shanti Kunj, Delhi - 110001"
    cart_items: Optional[List[CartItemInput]] = Field(default=None, description="Active confirmed cart items to export to ONDC Beckn")


class ONDCBecknExportResponse(BaseModel):
    beckn_schema_version: str = "1.2.0"
    domain: str = "ONDC:RET10"
    bpp_id: str = "kiranavaani.gnani.ai"
    status: str = "CONFIRMED"
    payload: Dict[str, Any]


# ---------------------------------------------------------
# Bhav Pucho (Price Inquiry & Budget Advisory) Schemas
# ---------------------------------------------------------
class PriceInquiryRequest(BaseModel):
    query: str = Field(..., examples=["Basmati chawal ka kya bhav hai?"])


class PriceQuoteItem(BaseModel):
    sku_id: str
    name_en: str
    name_hi: str
    category: str
    price_inr: float
    unit: str
    in_stock: bool


class PriceInquiryResponse(BaseModel):
    query: str
    found: bool
    items: List[PriceQuoteItem]
    spoken_answer_hi: str
    spoken_answer_en: str
    voice_audio_base64: Optional[str] = None
    voice_audio_format: str = "wav"


class BudgetAdvisorRequest(BaseModel):
    budget_inr: float = Field(..., examples=[500.0])
    mandatory_items: List[CartItemInput] = Field(default_factory=list)
    filler_product_query: Optional[str] = Field("sugar", description="Product to fill remaining budget with (e.g. sugar, tea, milk)")


class BudgetAdvisorResponse(BaseModel):
    budget_inr: float
    allocated_total_inr: float
    remaining_balance_inr: float
    mandatory_items_cost: float
    suggested_filler_item: Optional[CatalogueSKU] = None
    suggested_filler_quantity: Optional[float] = None
    advice_hi: str
    advice_en: str
    voice_audio_base64: Optional[str] = None
    voice_audio_format: str = "wav"


# ---------------------------------------------------------
# Kirana Soundbox 2.0 & Thermal POS Receipt Schemas
# ---------------------------------------------------------
class SoundboxChimeRequest(BaseModel):
    amount_inr: float = Field(..., examples=[106.0])
    store_name: str = Field("Gupta Kirana Store")
    customer_name: Optional[str] = None
    payment_mode: str = Field("UPI", description="'UPI', 'Cash', or 'Khata'")


class SoundboxChimeResponse(BaseModel):
    amount_inr: float
    chime_text_hi: str
    voice_audio_base64: Optional[str] = None
    voice_audio_format: str = "wav"
    timestamp: str
    is_mock: bool = False


class ThermalReceiptLine(BaseModel):
    sku_id: str
    name_en: str
    name_hi: str
    quantity: float
    unit: str
    rate: float
    total: float


class ThermalReceiptData(BaseModel):
    receipt_no: str
    store_name: str = "GUPTA KIRANA & GENERAL STORE"
    store_tagline: str = "Shudh Rashan • Vishwas Ka Prateek"
    fssai_lic: str = "13324999000182"
    gstin: str = "07AAAAA0000A1Z5"
    store_address: str = "Shop 4, Main Market, Block B, New Delhi - 110001"
    store_phone: str = "+91 98111-23456"
    customer_name: str = "Walk-in Customer"
    date_time: str
    items: List[ThermalReceiptLine]
    subtotal_inr: float
    cgst_inr: float
    sgst_inr: float
    delivery_fee_inr: float = 0.0
    total_inr: float
    savings_inr: float
    payment_mode: str
    upi_qr_string: str = ""


# ---------------------------------------------------------
# Voice Biometrics ("Awaaz Pehchaan") Schemas — Inspired by Gnani Armour360
# ---------------------------------------------------------
class VoiceprintVerificationRequest(BaseModel):
    customer_id: str = Field(..., examples=["CUST-001"], description="Customer ID in Khata Ledger")
    caller_phone: Optional[str] = Field("+91 98111-23456", description="Caller phone number")
    audio_base64: Optional[str] = Field(None, max_length=15_000_000, description="Audio payload for acoustic feature extraction (max ~10MB)")
    test_imposter_mode: bool = Field(False, description="Simulate an imposter trying to fraudulently charge this Khata")


class VoiceprintVerificationResponse(BaseModel):
    verified: bool
    customer_id: str
    customer_name: str
    match_score: float = Field(..., ge=0.0, le=1.0, description="Biometric acoustic similarity match (0.0 to 1.0)")
    confidence_tier: str = Field(..., description="'HIGH_CONFIDENCE_MATCH', 'SUSPICIOUS_REVIEW', or 'IMPOSTER_REJECTED'")
    voiceprint_hash: str = Field(..., description="Encrypted voiceprint biometric fingerprint hash")
    fundamental_freq_f0_hz: float = Field(..., description="Estimated fundamental vocal pitch frequency")
    formant_dispersion_hz: float = Field(..., description="Acoustic formant vocal tract resonance profile")
    spectral_centroid_hz: float = Field(..., description="Vocal timbre brightness centroid")
    jitter_percent: float = Field(..., description="Acoustic pitch stability index")
    shimmer_db: float = Field(..., description="Vocal amplitude perturbation index")
    auth_badge_text: str
    auth_message_hi: str
    auth_message_en: str
    khata_debit_permitted: bool
    voice_audio_base64: Optional[str] = None
    voice_audio_format: str = "wav"


# ---------------------------------------------------------
# B2B Mandi Wholesale Replenishment Schemas
# ---------------------------------------------------------
class MandiReorderTrigger(BaseModel):
    sku_id: str
    name_en: str
    name_hi: str
    current_stock: float
    unit: str
    reorder_threshold: float
    suggested_reorder_qty: float
    wholesale_rate_inr: float
    total_wholesale_cost_inr: float
    wholesaler_name: str = "Radhe Shyam Agro Mandi Wholesalers"
    wholesaler_phone: str = "+91 98765-43210"
    mandi_location: str = "APMC Yard, Grain Mandi, New Delhi"
    spoken_alert_hi: str
    spoken_alert_en: str
    whatsapp_po_text: str


class InventoryDepleteRequest(BaseModel):
    items: List[CartItemInput]
    order_id: Optional[str] = None


class InventoryStatusResponse(BaseModel):
    store_name: str
    total_skus: int
    low_stock_count: int
    reorder_triggers: List[MandiReorderTrigger]
    inventory_items: List[Dict[str, Any]]
    spoken_restock_prompt: Optional[str] = None


class MandiOrderDispatchRequest(BaseModel):
    sku_id: str
    reorder_quantity: float = Field(..., gt=0.0, le=5000.0, description="Replenishment quantity in units or kg")
    wholesaler_name: Optional[str] = "Radhe Shyam Agro Mandi Wholesalers"
    wholesaler_phone: Optional[str] = Field("+91 98765-43210", description="Wholesaler contact number")
    notes: Optional[str] = "Urgent Kirana morning delivery dispatch"


class MandiOrderDispatchResponse(BaseModel):
    po_id: str
    sku_id: str
    item_name: str
    quantity: float
    unit: str
    wholesale_rate_inr: float
    total_cost_inr: float
    wholesaler_name: str
    wholesaler_phone: str
    dispatch_status: str
    whatsapp_url: str
    spoken_confirmation_hi: str
    voice_audio_base64: Optional[str] = None
    voice_audio_format: str = "wav"


# ---------------------------------------------------------
# Telemetry Benchmark & Indic Stack vs US Cloud Schemas
# ---------------------------------------------------------
class TelemetryStage(BaseModel):
    stage_name: str
    latency_ms: float
    description: str


class StackComparisonItem(BaseModel):
    metric_name: str
    gnani_stack_val: str
    generic_us_cloud_val: str
    delta_advantage: str
    technical_reason: str


class TelemetryBenchmarkResponse(BaseModel):
    pipeline_total_latency_ms: float
    stages: List[TelemetryStage]
    comparisons: List[StackComparisonItem]
    indic_fraction_accuracy_pct: float
    zero_db_telephony_f1_pct: float
    cost_per_order_inr: float
    us_cost_per_order_inr: float
    savings_pct: float


# ---------------------------------------------------------
# Judge's Stress-Test Arena Schemas
# ---------------------------------------------------------
class JudgeStressTestCase(BaseModel):
    test_id: str
    title: str
    category: str
    difficulty_badge: str
    prompt_utterance: str
    audio_sample_url: Optional[str] = None
    adversarial_challenge: str
    why_naive_models_fail: str
    key_features_tested: List[str]


class JudgeStressTestResponse(BaseModel):
    test_id: str
    title: str
    utterance: str
    normalized_transcript: str
    latency_ms: float
    item_f1_score: float
    detected_intent: str
    parsed_items: List[ParsedItem]
    rules_applied: List[str]
    repairs: List[RepairedItemEvent] = Field(default_factory=list)
    voiceprint_status: Optional[str] = None
    explanation: str
    spoken_reply_hi: str


# ---------------------------------------------------------
# Bhaav-Taal (भाव-तोल) Kirana Bargaining Schemas
# ---------------------------------------------------------
class BargainItemDetail(BaseModel):
    sku_id: str
    name_en: str
    name_hi: str
    quantity: float
    unit: str
    retail_rate_inr: float
    wholesale_cost_inr: float
    offered_rate_inr: float
    line_original_inr: float
    line_discounted_inr: float
    margin_preserved_inr: float


class BhaavTaalRequest(BaseModel):
    transcript: Optional[str] = Field(None, max_length=1000)
    customer_id: Optional[str] = "CUST-001"
    customer_name: Optional[str] = Field("Sharma Ji (शर्मा जी)", max_length=100)
    cart_items: Optional[List[CartItemInput]] = None
    target_discount_pct: Optional[float] = Field(None, ge=0.0, le=100.0)


class BhaavTaalResponse(BaseModel):
    is_bargain_intent: bool
    customer_name: str
    loyalty_tier: str
    original_total_inr: float
    negotiated_total_inr: float
    total_savings_inr: float
    discount_pct: float
    merchant_margin_preserved_pct: float
    spoken_counter_offer_hi: str
    spoken_counter_offer_en: str
    bargain_items: List[BargainItemDetail]
    voice_audio_base64: Optional[str] = None
    voice_audio_format: str = "wav"


# ---------------------------------------------------------
# Chhotu Dispatch (किराना डिलीवरी राइडर) Schemas
# ---------------------------------------------------------
class DeliveryLandmarkInfo(BaseModel):
    has_delivery_intent: bool = False
    recipient_name: Optional[str] = None
    primary_landmark: Optional[str] = None
    house_or_floor_marker: Optional[str] = None
    delivery_time_window: Optional[str] = None
    payment_terms: str = "CASH_ON_DELIVERY"
    special_instructions: Optional[str] = None
    full_vernacular_address: str = ""


class RiderDispatchSlipRequest(BaseModel):
    order_id: Optional[str] = None
    customer_name: Optional[str] = Field("Sharma Ji (शर्मा जी)", max_length=100)
    transcript: Optional[str] = Field(None, max_length=1000)
    landmark_info: Optional[DeliveryLandmarkInfo] = None
    cart_items: Optional[List[CartItemInput]] = None
    total_amount_inr: Optional[float] = Field(None, ge=0.0, le=100000.0)
    rider_name: str = Field("Chhotu (छोटू)", max_length=100)
    rider_phone: str = Field("+91 98111-22334", max_length=25)


class RiderDispatchSlipResponse(BaseModel):
    dispatch_id: str
    order_id: str
    rider_name: str
    customer_name: str
    vernacular_route_directions: str
    delivery_window: str
    payment_collection_directive: str
    order_items_summary: str
    whatsapp_rider_text: str
    whatsapp_url: str
    rider_voice_note_hi: str
    voice_audio_base64: Optional[str] = None
    voice_audio_format: str = "wav"


# ---------------------------------------------------------
# Rasoi se Rashan (रसोई से राशन) Schemas
# ---------------------------------------------------------
class RecipeIngredientItem(BaseModel):
    sku_id: str
    name_en: str
    name_hi: str
    category: str
    quantity: float
    unit: str
    price_inr: float
    is_core_staple: bool = True
    in_stock: bool = True


class RecipeToCartRequest(BaseModel):
    dish_query: str = Field(..., max_length=500, examples=["Rajma Chawal for 4 people", "आज 4 लोगों के लिए राजमा चावल बनाना है"])
    servings: Optional[int] = Field(4, le=50, description="Servings count (clamped to positive)")
    include_seasonings: bool = True


class RecipeToCartResponse(BaseModel):
    dish_name_en: str
    dish_name_hi: str
    servings: int
    matched_ingredients: List[RecipeIngredientItem]
    bundle_subtotal_inr: float
    bundle_discount_inr: float
    bundle_total_inr: float
    spoken_recipe_prompt_hi: str
    spoken_recipe_prompt_en: str
    voice_audio_base64: Optional[str] = None
    voice_audio_format: str = "wav"



# ---------------------------------------------------------
# Awaaz-e-Jazbaat (Customer Urgency & Emotion Telemetry)
# Inspired by Gnani.ai call360 Speech Analytics
# ---------------------------------------------------------
class CustomerJazbaatInfo(BaseModel):
    urgency_level: str = Field("NORMAL", description="'TATKAL_EXPRESS_10MIN', 'HIGH', 'NORMAL', or 'CASUAL'")
    urgency_score: float = Field(0.2, ge=0.0, le=1.0)
    is_tatkal_priority: bool = False
    speech_tempo_wpm: float = Field(120.0, description="Estimated words per minute")
    detected_cues: List[str] = Field(default_factory=list)
    sentiment: str = Field("POLITE_NEUTRAL", description="'HURRIED_ANXIOUS', 'POLITE_NEUTRAL', 'FRUSTRATED', or 'PATIENT'")
    merchant_action_hint_hi: str = Field("सामान्य डिलीवरी", description="Actionable hint for store owner in Hindi")
    merchant_action_hint_en: str = Field("Standard delivery", description="Actionable hint for store owner in English")


# ---------------------------------------------------------
# Armour360 Acoustic Liveness & Anti-Spoofing Schemas
# Inspired by Gnani.ai Armour360 Voice Biometrics Anti-Fraud
# ---------------------------------------------------------
class LivenessCheckRequest(BaseModel):
    customer_id: str = Field("CUST-001", max_length=50)
    customer_name: Optional[str] = Field("Sharma Ji (शर्मा जी)", max_length=100)
    audio_base64: Optional[str] = Field(None, max_length=15_000_000, description="Audio payload for acoustic feature extraction (max ~10MB)")
    simulate_replay_attack: bool = False
    simulate_synthetic_voice: bool = False
    simulate_attack_type: Optional[str] = Field(None, description="Optional simulation preset: 'replay_attack' or 'ai_cloned_voice'")


class LivenessCheckResponse(BaseModel):
    customer_id: str
    customer_name: str
    is_live_human: bool
    liveness_score: float = Field(..., ge=0.0, le=1.0)
    verdict_badge: str = Field(..., description="'VERIFIED_LIVE_HUMAN', 'REPLAY_ATTACK_DETECTED', or 'SYNTHETIC_CLONE_DETECTED'")
    attack_type: Optional[str] = None
    spectral_flux: float
    jitter_percent: float
    shimmer_percent: float
    secondary_resonance_db: float
    diagnostic_details: str
    recommended_action: str = Field(..., description="'PROCEED_WITH_CREDIT', 'REQUIRE_OTP_VERIFICATION', or 'BLOCK_TRANSACTION'")
    security_prompt_hi: str

    @computed_field
    @property
    def is_live(self) -> bool:
        return self.is_live_human

    @computed_field
    @property
    def attack_detected(self) -> Optional[str]:
        return self.attack_type

    @computed_field
    @property
    def action_permitted(self) -> bool:
        return self.is_live_human and self.recommended_action == "PROCEED_WITH_CREDIT"

    @computed_field
    @property
    def jitter_ppq5(self) -> float:
        return self.jitter_percent

    @computed_field
    @property
    def loudspeaker_resonance_peak_db(self) -> float:
        return self.secondary_resonance_db

    @computed_field
    @property
    def analysis_text_en(self) -> str:
        return self.diagnostic_details

    @computed_field
    @property
    def analysis_text_hi(self) -> str:
        return self.security_prompt_hi


# ---------------------------------------------------------
# WhatsApp Voice Note Ingestion & Bot Schemas
# ---------------------------------------------------------
class WhatsAppVoiceNoteRequest(BaseModel):
    sender_name: str = Field("Sharma Ji (शर्मा जी)", max_length=100)
    sender_phone: str = Field("+91 98201-12345", max_length=25)
    audio_base64: Optional[str] = Field(None, max_length=15_000_000, description="Audio payload for WhatsApp voice note (max ~10MB)")
    audio_filename: str = Field("voice_note.ogg", max_length=100)
    preset_id: Optional[str] = None
    keyterms_enabled: bool = True


class WhatsAppVoiceNoteResponse(BaseModel):
    note_id: str
    sender_name: str
    sender_phone: str
    received_timestamp: str
    transcript: str
    parsed_items: List[ParsedItem]
    confirmed_skus_count: int
    cart_total_inr: float
    estimated_delivery_mins: int
    is_tatkal: bool
    upi_payment_link: str
    upi_qr_data: str
    whatsapp_auto_reply_text: str
    voice_audio_base64: Optional[str] = None
    voice_audio_format: str = "wav"


ProcessOrderResponse.model_rebuild()

