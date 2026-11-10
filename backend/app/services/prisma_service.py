"""
Gnani AI Prisma Speech-to-Text (STT) Integration Service.
Supports Prisma v3.0 REST STT with Auto-LID, code-mixed Hinglish output, and catalogue keyterms biasing.
Falls back to a realistic mock/demo mode when credentials are not configured or in offline testing.
"""
import logging
from typing import Optional, List, Tuple
import httpx

from backend.app.config import (
    GNANI_API_KEY,
    GNANI_STT_ENDPOINT,
    GNANI_STT_MODEL,
    is_live_gnani_configured,
    get_configured_api_keys
)
from backend.app.schemas import TranscriptionResponse

logger = logging.getLogger(__name__)

# Sample realistic Hinglish grocery audio transcripts for mock/demo mode
DEFAULT_MOCK_TRANSCRIPT = "Bhaiya do packet Maggi, ek kilo sugar aur aadha litre milk bhej dena."


class PrismaSTTService:
    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key if api_key is not None else GNANI_API_KEY
        self.endpoint = endpoint or GNANI_STT_ENDPOINT
        self.model = model or GNANI_STT_MODEL

    def is_configured(self) -> bool:
        """Checks if a valid live Gnani API key is configured."""
        return is_live_gnani_configured()

    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        filename: str = "audio.wav",
        keyterms: Optional[List[str]] = None,
        language_code: str = "indic-auto"
    ) -> TranscriptionResponse:
        """
        Transcribes audio bytes via Gnani AI Prisma REST API.
        If live credentials are unavailable, operates in clearly labelled mock mode.
        """
        api_keys = get_configured_api_keys()
        if not api_keys and self.api_key:
            api_keys = [self.api_key]

        if not api_keys:
            logger.info("Gnani Prisma API key not configured or demo key used. Using realistic mock transcription.")
            return TranscriptionResponse(
                transcript=DEFAULT_MOCK_TRANSCRIPT,
                language_detected="hi-Latn / hi-Deva (Code-Mixed Hinglish)",
                confidence=0.96,
                model=self.model,
                is_mock=True,
                duration_sec=3.5,
                note="Demo mode: Configured without live Gnani API key. Set GNANI_API_KEY in .env for live telephony STT."
            )

        form_data = {
            "model": self.model,
            "language_code": "hi-IN,en-IN" if language_code == "indic-auto" else language_code,
            "format": "codemix"
        }

        if keyterms:
            import json
            # Pass top 200 catalogue keyterms to bias beam search
            form_data["keyterms"] = json.dumps(keyterms[:200])

        content_type = "audio/wav"
        if filename.endswith(".webm"):
            content_type = "audio/webm"
        elif filename.endswith(".mp3"):
            content_type = "audio/mp3"
        elif filename.endswith(".ogg"):
            content_type = "audio/ogg"

        files = {
            "audio_file": (filename, audio_bytes, content_type)
        }

        last_status = None
        for key in api_keys:
            headers = {
                "X-API-Key-ID": key
            }
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    logger.info(f"Dispatching STT request to Gnani Prisma at {self.endpoint} with model={self.model}")
                    response = await client.post(
                        self.endpoint,
                        headers=headers,
                        data=form_data,
                        files=files
                    )

                last_status = response.status_code
                if response.status_code == 200:
                    data = response.json()
                    logger.info("Received successful transcription from Gnani Prisma API.")
                    transcript_text = data.get("transcript") or data.get("text") or data.get("data", {}).get("transcript", "")
                    confidence = float(data.get("confidence", 0.94))
                    lang = data.get("language") or data.get("detected_language") or "indic-auto (Hinglish)"

                    return TranscriptionResponse(
                        transcript=transcript_text,
                        language_detected=lang,
                        confidence=confidence,
                        model=self.model,
                        is_mock=False,
                        duration_sec=data.get("audio_duration")
                    )
                elif response.status_code in (401, 403, 429) and len(api_keys) > 1:
                    logger.warning(f"Gnani Prisma returned {response.status_code} with current key, attempting fallback key...")
                    continue
            except Exception as exc:
                logger.warning(f"Error attempting Gnani Prisma call: {exc}")
                continue

        logger.warning(
            f"Gnani Prisma requests exhausted (last HTTP {last_status}). Falling back to mock transcription."
        )
        return TranscriptionResponse(
            transcript=DEFAULT_MOCK_TRANSCRIPT,
            language_detected="hi-Latn (Fallback Mock)",
            confidence=0.88,
            model=self.model,
            is_mock=True,
            note=f"Fallback due to upstream Gnani API status {last_status}"
        )


# Default singleton instance
prisma_service = PrismaSTTService()
