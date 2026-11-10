"""
Unit tests for Noise Lab simulation and evaluation metrics.
Tests SNR calculation, ITU-T G.711 mu-law codec, WER, and Item-level F1 calculation.
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
