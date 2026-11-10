"""
Pydantic data models for KiranaVaani API requests and responses.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


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


class ParseOrderRequest(BaseModel):
    transcript: str = Field(..., examples=["Bhaiya do packet Maggi, ek kilo sugar aur aadha litre milk bhej dena."])
    keyterms_enabled: bool = Field(True, description="Enable catalogue keyterms biasing")


class ParseOrderResponse(BaseModel):
    raw_transcript: str
    normalized_transcript: str
    items: List[ParsedItem]
    is_order_complete: bool = Field(False, description="True if caller expressed completion e.g. 'bas itna hi'")
    khata_info: Optional[KhataInfo] = None


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
    items: List[ParsedItem]
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
    quantity: float
    unit: Optional[str] = None


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
    transcript: Optional[str] = None
    audio_base64: Optional[str] = None
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
    customer_id: str
    amount_paid_inr: float
    payment_mode: str = "cash"


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


class ONDCBecknExportResponse(BaseModel):
    beckn_schema_version: str = "1.2.0"
    domain: str = "ONDC:RET10"
    bpp_id: str = "kiranavaani.gnani.ai"
    status: str = "CONFIRMED"
    payload: Dict[str, Any]
