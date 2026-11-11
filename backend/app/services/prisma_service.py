"""
Gnani AI Prisma Speech-to-Text (STT) Integration Service.
Supports Prisma v3.0 REST STT with Auto-LID, code-mixed Hinglish output, and catalogue keyterms biasing.
Falls back to a realistic mock/demo mode when credentials are not configured or in offline testing.
"""
import asyncio
import logging
import subprocess
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


def is_wav_audio(audio_bytes: bytes) -> bool:
    """Returns True if the byte stream starts with a standard RIFF/WAVE header."""
    return len(audio_bytes) >= 12 and audio_bytes[:4] == b"RIFF" and audio_bytes[8:12] == b"WAVE"


async def convert_audio_to_wav(audio_bytes: bytes, filename: str = "audio.wav") -> Tuple[bytes, str]:
    """
    Transcodes incoming audio (WebM, OGG, MP4, AAC, or arbitrary codecs)
    into 16 kHz 16-bit mono PCM WAV accepted by Gnani AI Prisma v3.0 STT API.
    If the bytes are already WAV, bypasses conversion.
    """
    if not audio_bytes:
        return audio_bytes, filename

    if is_wav_audio(audio_bytes):
        return audio_bytes, "audio.wav"

    proc = None
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y", "-i", "pipe:0", "-ar", "16000", "-ac", "1", "-f", "wav", "pipe:1",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(input=audio_bytes), timeout=10.0)
        if proc.returncode == 0 and len(stdout) > 44:
            logger.info(f"FFmpeg successfully converted input audio ({len(audio_bytes)} B) to 16kHz WAV ({len(stdout)} B).")
            return stdout, "audio.wav"
        else:
            err_msg = stderr.decode("utf-8", errors="ignore")[:250]
            logger.warning(f"FFmpeg transcode non-zero exit ({proc.returncode}): {err_msg}")
    except (asyncio.TimeoutError, TimeoutError):
        if proc:
            try:
                proc.kill()
                await proc.wait()
            except Exception:
                pass
        logger.warning("FFmpeg transcode timed out after 10.0s.")
    except FileNotFoundError:
        logger.warning("FFmpeg executable not found in system PATH. Sending original audio bytes.")
    except Exception as e:
        logger.warning(f"Audio conversion error: {e}")

    return audio_bytes, filename


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
        self._semaphore: Optional[asyncio.Semaphore] = None

    @property
    def semaphore(self) -> asyncio.Semaphore:
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(value=3)
        return self._semaphore

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
        if audio_bytes is None:
            return TranscriptionResponse(
                transcript=DEFAULT_MOCK_TRANSCRIPT,
                language_detected="hi-Latn / hi-Deva (Code-Mixed Hinglish)",
                confidence=0.96,
                model=self.model,
                is_mock=True,
                duration_sec=3.5,
                note="Demo/mock mode: Default reference sample returned."
            )

        if len(audio_bytes) < 32:
            return TranscriptionResponse(
                transcript="",
                language_detected="und",
                confidence=0.0,
                model=self.model,
                is_mock=False,
                duration_sec=0.0,
                note="Microphone audio empty or too short."
            )

        api_keys = get_configured_api_keys()
        if not api_keys and self.api_key:
            api_keys = [self.api_key]

        if not api_keys:
            logger.info("Gnani Prisma API key not configured or demo key used.")
            if audio_bytes is None:
                return TranscriptionResponse(
                    transcript=DEFAULT_MOCK_TRANSCRIPT,
                    language_detected="hi-Latn / hi-Deva (Code-Mixed Hinglish)",
                    confidence=0.96,
                    model=self.model,
                    is_mock=True,
                    duration_sec=3.5,
                    note="Demo mode: Configured without live Gnani API key. Set GNANI_API_KEY in .env for live telephony STT."
                )
            else:
                return TranscriptionResponse(
                    transcript="",
                    language_detected="und",
                    confidence=0.0,
                    model=self.model,
                    is_mock=False,
                    duration_sec=0.0,
                    note="No Gnani API key configured to transcribe live audio."
                )

        # Transcode incoming audio (e.g. WebM/Opus from browser MediaRecorder) to 16 kHz mono WAV
        audio_bytes, filename = await convert_audio_to_wav(audio_bytes, filename)

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
        async with self.semaphore:
            async with httpx.AsyncClient(timeout=15.0) as client:
                for attempt in range(2):
                    for key in api_keys:
                        headers = {
                            "X-API-Key-ID": key
                        }
                        try:
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
                                transcript_text = (
                                    data.get("transcript")
                                    or data.get("text")
                                    or data.get("data", {}).get("transcript", "")
                                )
                                confidence = float(data.get("confidence", 0.94))
                                lang = data.get("language") or data.get("detected_language") or "indic-auto (Hinglish)"

                                return TranscriptionResponse(
                                    transcript=transcript_text.strip(),
                                    language_detected=lang,
                                    confidence=confidence,
                                    model=self.model,
                                    is_mock=False,
                                    duration_sec=data.get("audio_duration")
                                )
                            elif response.status_code == 429:
                                logger.warning(f"Gnani Prisma 429 rate limit (attempt {attempt+1}). Sleeping 0.8s before retry...")
                                await asyncio.sleep(0.8)
                                continue
                            elif response.status_code in (401, 403) and len(api_keys) > 1:
                                logger.warning(f"Gnani Prisma returned {response.status_code} with current key, attempting fallback key...")
                                continue
                            else:
                                try:
                                    err_payload = response.json()
                                    logger.warning(f"Gnani Prisma returned HTTP {response.status_code}: {err_payload}")
                                except Exception:
                                    logger.warning(f"Gnani Prisma returned HTTP {response.status_code}: {response.text[:200]}")
                        except Exception as exc:
                            logger.warning(f"Error attempting Gnani Prisma call: {exc}")
                            continue

        logger.warning(
            f"Gnani Prisma requests exhausted (last HTTP {last_status})."
        )
        if api_keys:
            return TranscriptionResponse(
                transcript="",
                language_detected="und",
                confidence=0.0,
                model=self.model,
                is_mock=False,
                note=f"Upstream Gnani STT service unavailable (HTTP {last_status}). Please try speaking again."
            )
        return TranscriptionResponse(
            transcript="",
            language_detected="und",
            confidence=0.0,
            model=self.model,
            is_mock=False,
            note=f"Upstream Gnani STT service unavailable (HTTP {last_status}). Please try speaking again."
        )


# Default singleton instance
prisma_service = PrismaSTTService()
