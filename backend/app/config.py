"""
Configuration settings for KiranaVaani backend.
Reads configuration from environment variables with graceful fallback for local development and mock testing.
"""
import os
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CATALOGUE_PATH = DATA_DIR / "catalogue.json"
ALT_CATALOGUE_PATH = Path(__file__).resolve().parent / "data" / "grocery_catalogue.json"

# Gnani AI API Configuration
GNANI_API_KEY: Optional[str] = os.getenv("GNANI_API_KEY", "").strip() or None
GNANI_STT_ENDPOINT: str = os.getenv("GNANI_STT_ENDPOINT", "https://api.vachana.ai/stt/v3").strip()
GNANI_TTS_ENDPOINT: str = os.getenv("GNANI_TTS_ENDPOINT", "https://api.vachana.ai/api/v1/tts/inference").strip()
GNANI_STT_MODEL: str = os.getenv("GNANI_STT_MODEL", "prisma-v3.0").strip()
GNANI_TTS_MODEL: str = os.getenv("GNANI_TTS_MODEL", "timbre-v2.5").strip()

# Server settings
HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

# Minimum confidence threshold for automatic matching without clarification
CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.78"))
AMBIGUITY_DELTA_THRESHOLD: float = float(os.getenv("AMBIGUITY_DELTA_THRESHOLD", "0.12"))


def is_live_gnani_configured() -> bool:
    """Returns True only if a non-placeholder Gnani API key is configured."""
    if not GNANI_API_KEY:
        return False
    # Check for known mock/placeholder values
    lower_key = GNANI_API_KEY.lower()
    if any(placeholder in lower_key for placeholder in ("demo", "test", "fake", "placeholder", "xxx", "your_")):
        return False
    return len(GNANI_API_KEY) >= 16


def get_catalogue_path() -> Path:
    """Returns the existing catalogue path."""
    if CATALOGUE_PATH.exists():
        return CATALOGUE_PATH
    if ALT_CATALOGUE_PATH.exists():
        return ALT_CATALOGUE_PATH
    return CATALOGUE_PATH
