"""
Health check endpoint for KiranaVaani backend.
"""
from fastapi import APIRouter
from backend.app.schemas import HealthResponse
from backend.app.config import is_live_gnani_configured, GNANI_STT_MODEL, GNANI_TTS_MODEL
from backend.app.services.catalogue_matcher import catalogue_matcher

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def get_health():
    """Returns the operational status, Gnani AI integration state, and catalogue statistics."""
    skus = catalogue_matcher.get_all_skus()
    live_configured = is_live_gnani_configured()
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        service="KiranaVaani Backend",
        gnani_live_configured=live_configured,
        live_api_configured=live_configured,
        gnani_stt_model=GNANI_STT_MODEL,
        gnani_tts_model=GNANI_TTS_MODEL,
        catalogue_sku_count=len(skus),
        supported_languages=["hi-IN", "en-IN", "Hinglish (Code-Mixed)"]
    )
