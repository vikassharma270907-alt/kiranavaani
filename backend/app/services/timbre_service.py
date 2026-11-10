"""
Gnani AI Timbre Text-to-Speech (TTS) Integration Service.
Supports Timbre v2.5 / v3.0 REST speech synthesis with natural Indian prosody and Hindi/Hinglish phonetics.
Generates valid playable fallback audio when credentials are not configured or in offline mode.
"""
import base64
import io
import math
import logging
import struct
import wave
from typing import Optional
import httpx

from backend.app.config import (
    GNANI_API_KEY,
    GNANI_TTS_ENDPOINT,
    GNANI_TTS_MODEL,
    is_live_gnani_configured
)
from backend.app.schemas import SynthesizeResponse

logger = logging.getLogger(__name__)


def generate_mock_wav_chime(duration_sec: float = 1.5, sample_rate: int = 16000) -> bytes:
    """
    Generates a valid, playable synthetic confirmation chime as WAV bytes.
    Ensures frontend audio playback operates seamlessly even without active cloud TTS credentials.
    """
    num_samples = int(duration_sec * sample_rate)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit PCM
        wav_file.setframerate(sample_rate)

        # Generate a pleasant two-tone confirmation chord (523.25 Hz C5 + 659.25 Hz E5)
        frames = bytearray()
        for i in range(num_samples):
            t = float(i) / sample_rate
            envelope = math.exp(-3.0 * (t / duration_sec))  # Exponential decay
            val1 = math.sin(2.0 * math.pi * 523.25 * t)
            val2 = math.sin(2.0 * math.pi * 659.25 * t)
            sample_val = int(envelope * (val1 * 0.4 + val2 * 0.4) * 32767)
            sample_val = max(-32768, min(32767, sample_val))
            frames.extend(struct.pack("<h", sample_val))

        wav_file.writeframes(frames)
    return buf.getvalue()


class TimbreTTSService:
    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key if api_key is not None else GNANI_API_KEY
        self.endpoint = endpoint or GNANI_TTS_ENDPOINT
        self.model = model or GNANI_TTS_MODEL

    def is_configured(self) -> bool:
        """Returns True if a valid live Gnani API key is configured."""
        return is_live_gnani_configured()

    async def synthesize_speech(
        self,
        text: str,
        voice: str = "Nalini",
        language: str = "hi-IN",
        speed: float = 1.0
    ) -> SynthesizeResponse:
        """
        Synthesizes text into spoken audio using Gnani AI Timbre REST API.
        Falls back to valid synthetic WAV chime when credentials are not configured.
        """
        if not self.is_configured():
            logger.info("Gnani Timbre API key not configured. Generating synthetic playback audio.")
            mock_audio_bytes = generate_mock_wav_chime(duration_sec=1.2)
            mock_b64 = base64.b64encode(mock_audio_bytes).decode("utf-8")
            return SynthesizeResponse(
                text=text,
                audio_base64=mock_b64,
                audio_format="wav",
                duration_sec=1.2,
                is_mock=True,
                voice=voice,
                model=self.model,
                note="Demo mode: Configured without live Gnani API key. Set GNANI_API_KEY in .env for live Timbre voice synthesis."
            )

        headers = {
            "X-API-Key-ID": self.api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "text": text,
            "voice": voice,
            "model": self.model,
            "language": language,
            "speed": speed,
            "audio_config": {
                "sample_rate": 24000,
                "num_channels": 1,
                "sample_width": 2,
                "encoding": "linear_pcm",
                "container": "wav"
            }
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                logger.info(f"Dispatching TTS request to Gnani Timbre at {self.endpoint}")
                response = await client.post(
                    self.endpoint,
                    headers=headers,
                    json=payload
                )

            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                if "audio" in content_type or "octet-stream" in content_type:
                    # Raw audio bytes returned
                    audio_bytes = response.content
                    b64 = base64.b64encode(audio_bytes).decode("utf-8")
                else:
                    data = response.json()
                    raw_b64 = data.get("audio_content") or data.get("audio_base64") or ""
                    b64 = raw_b64

                logger.info("Received synthesized audio from Gnani Timbre API.")
                return SynthesizeResponse(
                    text=text,
                    audio_base64=b64,
                    audio_format="wav",
                    duration_sec=max(1.0, len(text) * 0.08),
                    is_mock=False,
                    voice=voice,
                    model=self.model
                )
            else:
                logger.warning(
                    f"Gnani Timbre returned HTTP {response.status_code}: {response.text}. "
                    "Using fallback audio."
                )
                mock_audio_bytes = generate_mock_wav_chime()
                return SynthesizeResponse(
                    text=text,
                    audio_base64=base64.b64encode(mock_audio_bytes).decode("utf-8"),
                    audio_format="wav",
                    duration_sec=1.2,
                    is_mock=True,
                    voice=voice,
                    model=self.model,
                    note=f"Fallback due to upstream HTTP {response.status_code}"
                )

        except Exception as exc:
            logger.error(f"Error calling Gnani Timbre API: {exc}. Using fallback audio.", exc_info=True)
            mock_audio_bytes = generate_mock_wav_chime()
            return SynthesizeResponse(
                text=text,
                audio_base64=base64.b64encode(mock_audio_bytes).decode("utf-8"),
                audio_format="wav",
                duration_sec=1.2,
                is_mock=True,
                voice=voice,
                model=self.model,
                note=f"Fallback due to error: {str(exc)}"
            )


# Default singleton instance
timbre_service = TimbreTTSService()
