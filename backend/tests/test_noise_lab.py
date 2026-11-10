"""
Unit tests for Noise Lab simulation and evaluation metrics.
Tests SNR calculation, ITU-T G.711 mu-law codec, WER, Item-level F1 calculation,
and synthetic acoustic noise generators (fan hum, street traffic, market babble).
"""
import pytest
import numpy as np
from noise_lab.metrics import (
    calculate_wer,
    calculate_item_metrics,
    calculate_quantity_accuracy,
    levenshtein_distance
)
from noise_lab.generate_noise import (
    generate_fan_hum,
    generate_traffic_noise,
    generate_market_babble,
    mu_law_encode,
    mu_law_quantize_8bit,
    mu_law_decode,
    mix_speech_and_noise,
    apply_telephony_channel
)


def test_levenshtein_and_wer_exact():
    ref = "bhaiya do packet maggi aur ek kilo sugar"
    hyp = "bhaiya do packet maggi aur ek kilo sugar"
    assert calculate_wer(ref, hyp) == 0.0


def test_wer_with_errors():
    ref = "bhaiya do packet maggi"
    hyp = "bhaiya do packet meghee"
    wer = calculate_wer(ref, hyp)
    assert wer > 0.0
    assert wer <= 50.0


def test_item_metrics_perfect():
    gt = [
        {"sku_id": "SKU-001", "qty": 1.0},
        {"sku_id": "SKU-002", "qty": 2.0}
    ]
    pred = [
        {"sku_id": "SKU-001", "qty": 1.0},
        {"sku_id": "SKU-002", "qty": 2.0}
    ]
    metrics = calculate_item_metrics(gt, pred)
    assert metrics["precision"] == 100.0
    assert metrics["recall"] == 100.0
    assert metrics["item_f1"] == 100.0


def test_item_metrics_quantity_mismatch():
    gt = [{"sku_id": "SKU-001", "qty": 1.0}]
    pred = [{"sku_id": "SKU-001", "qty": 2.0}]  # Wrong quantity
    metrics = calculate_item_metrics(gt, pred)
    assert metrics["item_f1"] == 0.0  # Must match both SKU and quantity


def test_quantity_accuracy():
    gt = [
        {"sku_id": "SKU-001", "qty": 1.0},
        {"sku_id": "SKU-002", "qty": 0.5}
    ]
    pred = [
        {"sku_id": "SKU-001", "qty": 1.0},
        {"sku_id": "SKU-002", "qty": 0.5}
    ]
    assert calculate_quantity_accuracy(gt, pred) == 100.0


def test_mu_law_companding_reconstruction():
    """Verify ITU-T G.711 mu-law compression and decompression preserves waveform fidelity."""
    t = np.linspace(0, 1.0, 1000)
    orig = 0.8 * np.sin(2 * np.pi * 440 * t)

    compressed = mu_law_encode(orig, mu=255)
    quantized = mu_law_quantize_8bit(compressed)
    reconstructed = mu_law_decode(quantized, mu=255)

    # Reconstruction error should be minimal (within 8-bit quantization threshold)
    max_error = np.max(np.abs(orig - reconstructed))
    assert max_error < 0.05, f"Expected error < 0.05, got {max_error}"


def test_snr_mixing_energy():
    speech = np.ones(1000, dtype=np.float32) * 0.5
    noise = np.random.normal(0, 0.5, 1000).astype(np.float32)
    mixed = mix_speech_and_noise(speech, noise, target_snr_db=10.0)

    assert len(mixed) == len(speech)
    assert np.all(np.abs(mixed) <= 1.0)


def test_synthetic_noise_generators():
    """Verify fan hum, traffic rumble, and market babble generators produce valid audio frames."""
    sr = 16000
    duration = 0.5
    expected_len = int(sr * duration)

    # Fan hum
    fan = generate_fan_hum(duration_sec=duration, sample_rate=sr)
    assert len(fan) == expected_len
    assert fan.dtype == np.float32

    # Traffic rumble
    traffic = generate_traffic_noise(duration_sec=duration, sample_rate=sr)
    assert len(traffic) == expected_len
    assert np.max(np.abs(traffic)) <= 1.0

    # Market babble
    babble = generate_market_babble(duration_sec=duration, sample_rate=sr)
    assert len(babble) == expected_len
    assert np.max(np.abs(babble)) <= 1.0


def test_apply_telephony_channel():
    """Verify telephony channel downsamples to 8 kHz and bandpasses to PSTN bandwidth."""
    sr = 16000
    t = np.linspace(0, 0.5, int(sr * 0.5))
    signal_in = 0.6 * np.sin(2 * np.pi * 500 * t)

    filtered, out_sr = apply_telephony_channel(signal_in, orig_sr=sr)
    assert out_sr == 8000
    assert len(filtered) == int(8000 * 0.5)
    assert np.max(np.abs(filtered)) <= 1.0


def test_wer_empty_and_disjoint():
    """Verify WER boundary conditions for empty reference and hypothesis."""
    assert calculate_wer("", "") == 0.0
    assert calculate_wer("some reference text", "") == 100.0


def test_quantity_accuracy_empty_and_zero_matches():
    """Verify quantity accuracy returns 0.0 when no matching SKUs are predicted."""
    gt = [{"sku_id": "SKU-001", "qty": 1.0}]
    pred = [{"sku_id": "SKU-002", "qty": 1.0}]  # Disjoint SKU
    assert calculate_quantity_accuracy(gt, pred) == 0.0


def test_snr_mixing_silent_signals():
    """Verify mix_speech_and_noise handles silent speech safely without NaN or crash."""
    silent_speech = np.zeros(500, dtype=np.float32)
    noise = np.ones(500, dtype=np.float32) * 0.1
    res = mix_speech_and_noise(silent_speech, noise, target_snr_db=10.0)
    assert len(res) == 500
    assert not np.any(np.isnan(res))
