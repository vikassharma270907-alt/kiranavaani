"""
Configuration settings for KiranaVaani backend.
Reads configuration from environment variables with graceful fallback for local development and mock testing.
"""
import os
from pathlib import Path
from typing import Optional
try:
    from dotenv import load_dotenv
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    BACKEND_DIR = Path(__file__).resolve().parent.parent
    load_dotenv(dotenv_path=BASE_DIR.parent / "backend" / ".env")
    load_dotenv(dotenv_path=BASE_DIR / "backend" / ".env")
    load_dotenv(dotenv_path=BASE_DIR / ".env")
    load_dotenv()
except ImportError:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    BACKEND_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
CATALOGUE_PATH = DATA_DIR / "catalogue.json"
ALT_CATALOGUE_PATH = Path(__file__).resolve().parent / "data" / "grocery_catalogue.json"

# Gnani AI API Configuration
GNANI_API_KEY: Optional[str] = os.getenv("GNANI_API_KEY", "").strip() or None
GNANI_STT_ENDPOINT: str = os.getenv("GNANI_STT_URL", os.getenv("GNANI_STT_ENDPOINT", "https://api.vachana.ai/stt/v3")).strip()
GNANI_TTS_ENDPOINT: str = os.getenv("GNANI_TTS_URL", os.getenv("GNANI_TTS_ENDPOINT", "https://api.vachana.ai/api/v1/tts/inference")).strip()
GNANI_STT_MODEL: str = os.getenv("GNANI_STT_MODEL", "prisma-v3.0").strip()
GNANI_TTS_MODEL: str = os.getenv("GNANI_TTS_MODEL", "timbre-v2.5").strip()

# Server settings
HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", os.getenv("BACKEND_PORT", "8000")))
DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

# Minimum confidence threshold for automatic matching without clarification
CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.78"))
AMBIGUITY_DELTA_THRESHOLD: float = float(os.getenv("AMBIGUITY_DELTA_THRESHOLD", "0.12"))


def get_configured_api_keys() -> list[str]:
    """Returns all configured Gnani API keys in order of precedence."""
    keys: list[str] = []
    primary = (os.getenv("GNANI_API_KEY") or GNANI_API_KEY or "").strip()
    if primary and primary not in keys:
        keys.append(primary)
    fallback = (os.getenv("GNANI_API_KEY_FALLBACK") or os.getenv("GNANI_API_KEY_SECONDARY") or "").strip()
    if fallback and fallback not in keys:
        keys.append(fallback)
    raw_keys = os.getenv("GNANI_API_KEYS", "")
    if raw_keys:
        for k in raw_keys.split(","):
            k = k.strip()
            if k and k not in keys:
                keys.append(k)
    return [k for k in keys if k.startswith("vach_")]


def is_live_gnani_configured() -> bool:
    """Returns True only if a valid Gnani API key starting with vach_ is configured."""
    return len(get_configured_api_keys()) > 0


def get_catalogue_path() -> Path:
    """Returns the existing catalogue path."""
    if CATALOGUE_PATH.exists():
        return CATALOGUE_PATH
    if ALT_CATALOGUE_PATH.exists():
        return ALT_CATALOGUE_PATH
    return CATALOGUE_PATH
