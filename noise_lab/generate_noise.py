"""
Noise Generation & Telephony Channel Simulation Module.
Generates synthetic background noises (shop fan, street traffic, market babble),
simulates ITU-T G.711 mu-law 8 kHz telephone codec, and mixes signals at specified SNR levels.
"""
import math
from typing import Tuple, Optional
import numpy as np
from scipy import signal
import soundfile as sf


def generate_fan_hum(duration_sec: float, sample_rate: int = 16000) -> np.ndarray:
    """Generates synthetic 50 Hz electric motor hum with 100 Hz and 150 Hz harmonics."""
    num_samples = int(duration_sec * sample_rate)
    t = np.linspace(0, duration_sec, num_samples, endpoint=False)
    # 50 Hz fundamental + 100 Hz 2nd harmonic + 150 Hz 3rd harmonic + broadband turbulence
    hum = (
        0.55 * np.sin(2 * np.pi * 50 * t) +
        0.25 * np.sin(2 * np.pi * 100 * t) +
        0.12 * np.sin(2 * np.pi * 150 * t) +
        0.08 * np.random.normal(0, 0.1, num_samples)
    )
    return hum.astype(np.float32)


def generate_traffic_noise(duration_sec: float, sample_rate: int = 16000) -> np.ndarray:
    """Generates low-frequency vehicle engine rumble and road friction noise."""
    num_samples = int(duration_sec * sample_rate)
    white = np.random.normal(0, 1.0, num_samples)
    # Apply 2nd order lowpass filter at 400 Hz for engine rumble
    nyquist = 0.5 * sample_rate
    b, a = signal.butter(2, 400.0 / nyquist, btype="low")
    rumble = signal.lfilter(b, a, white)
    # Add occasional horn frequencies (450 Hz + 600 Hz pulses)
    t = np.linspace(0, duration_sec, num_samples, endpoint=False)
    horn_mask = (np.sin(2 * np.pi * 0.3 * t) > 0.85).astype(float)
    horns = 0.3 * horn_mask * (np.sin(2 * np.pi * 440 * t) + np.sin(2 * np.pi * 580 * t))
    combined = rumble + horns
    return (combined / (np.max(np.abs(combined)) + 1e-8)).astype(np.float32)


def generate_market_babble(duration_sec: float, sample_rate: int = 16000) -> np.ndarray:
    """Generates synthetic crowded kirana market chatter (multi-talker speech-shaped noise)."""
    num_samples = int(duration_sec * sample_rate)
    white = np.random.normal(0, 1.0, num_samples)
    # Bandpass filter around typical human vocal formants (200 Hz - 2800 Hz)
    nyquist = 0.5 * sample_rate
    b, a = signal.butter(3, [200.0 / nyquist, 2800.0 / nyquist], btype="band")
    babble = signal.lfilter(b, a, white)
    # Modulate envelope to mimic rhythmic conversational pauses
    t = np.linspace(0, duration_sec, num_samples, endpoint=False)
    mod = 0.6 + 0.4 * np.sin(2 * np.pi * 3.5 * t) * np.sin(2 * np.pi * 1.8 * t)
    modulated = babble * mod
    return (modulated / (np.max(np.abs(modulated)) + 1e-8)).astype(np.float32)


def mu_law_encode(x: np.ndarray, mu: int = 255) -> np.ndarray:
    """
    ITU-T G.711 mu-law logarithmic companding:
    F(x) = sgn(x) * ln(1 + mu*|x|) / ln(1 + mu), -1 <= x <= 1
    """
    clipped = np.clip(x, -1.0, 1.0)
    return np.sign(clipped) * np.log1p(mu * np.abs(clipped)) / np.log1p(mu)


def mu_law_quantize_8bit(compressed: np.ndarray) -> np.ndarray:
    """Quantizes compressed signal to discrete 8-bit telephony levels (-128 to 127)."""
    scaled = np.round((compressed + 1.0) * 127.5)
    quantized = np.clip(scaled, 0.0, 255.0)
    return (quantized / 127.5) - 1.0


def mu_law_decode(y: np.ndarray, mu: int = 255) -> np.ndarray:
    """
    ITU-T G.711 mu-law expansion (inverse transform):
    F^-1(y) = sgn(y) * (1 / mu) * ((1 + mu)^|y| - 1)
    """
    clipped = np.clip(y, -1.0, 1.0)
    return np.sign(clipped) * (1.0 / mu) * (np.power(1.0 + mu, np.abs(clipped)) - 1.0)


def apply_telephony_channel(
    audio: np.ndarray,
    orig_sr: int = 16000
) -> Tuple[np.ndarray, int]:
    """
    Simulates standard PSTN telephone channel:
    1. Downsamples from orig_sr (16 kHz) to 8 kHz telephony rate.
    2. Applies ITU-T 300 Hz - 3400 Hz telephone bandpass filter.
    3. Applies ITU-T G.711 mu-law 8-bit companding and quantization.
    """
    target_sr = 8000
    if orig_sr != target_sr:
        num_samples = int(round(len(audio) * float(target_sr) / orig_sr))
        resampled = signal.resample(audio, num_samples)
    else:
        resampled = audio.copy()

    # Bandpass filter (300 Hz - 3400 Hz telephone band)
    nyquist = 0.5 * target_sr
    low = 300.0 / nyquist
    high = min(3400.0 / nyquist, 0.99)
    b, a = signal.butter(4, [low, high], btype="band")
    filtered = signal.lfilter(b, a, resampled)

    # Normalize before mu-law
    peak = np.max(np.abs(filtered))
    if peak > 0:
        filtered = filtered / peak

    # Apply ITU-T G.711 mu-law companding & 8-bit quantization
    compressed = mu_law_encode(filtered, mu=255)
    quantized = mu_law_quantize_8bit(compressed)
    reconstructed = mu_law_decode(quantized, mu=255)

    return reconstructed.astype(np.float32), target_sr


def mix_speech_and_noise(
    speech: np.ndarray,
    noise: np.ndarray,
    target_snr_db: float
) -> np.ndarray:
    """
    Mixes speech and noise signals at a target Signal-to-Noise Ratio (SNR in dB):
    alpha = sqrt( P_speech / (P_noise * 10^(SNR / 10)) )
    mixed = speech + alpha * noise
    """
    p_speech = np.mean(speech ** 2)
    if p_speech <= 1e-12:
        return speech

    # Match noise length to speech
    if len(noise) < len(speech):
        repeats = int(np.ceil(len(speech) / len(noise)))
        noise = np.tile(noise, repeats)[:len(speech)]
    else:
        noise = noise[:len(speech)]

    p_noise = np.mean(noise ** 2)
    if p_noise <= 1e-12:
        return speech

    snr_linear = 10.0 ** (target_snr_db / 10.0)
    alpha = np.sqrt(p_speech / (p_noise * snr_linear))
    mixed = speech + alpha * noise

    # Normalize to [-1.0, 1.0] to prevent digital clipping
    max_val = np.max(np.abs(mixed))
    if max_val > 1.0:
        mixed = mixed / max_val

    return mixed.astype(np.float32)
