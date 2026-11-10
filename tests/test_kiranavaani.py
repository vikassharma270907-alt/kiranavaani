import pytest
import numpy as np
from fastapi.testclient import TestClient
from backend.main import app
from backend.parser import HinglishOrderParser
from backend.noise_lab import NoiseLab

@pytest.fixture
def parser():
    return HinglishOrderParser()

@pytest.fixture
def noise_lab(parser):
    return NoiseLab(parser=parser)

@pytest.fixture
def client():
    return TestClient(app)

def test_catalog_skus_count(parser):
    assert len(parser.skus) == 35
    assert len(parser.keyterms) <= 200
    assert len(parser.keyterms) >= 50

def test_colloquial_numeral_normalization(parser):
    assert "2.25" in parser.normalize_numerals("सवा दो किलो")
    assert "2.5" in parser.normalize_numerals("ढाई किलो")
    assert "1.5" in parser.normalize_numerals("डेढ़ किलो")
    assert "0.5" in parser.normalize_numerals("आधा किलो")
    assert "0.25" in parser.normalize_numerals("पाव भर")

def test_keyterm_bias_recovery(parser):
    # With keyterms ON
    res_on = parser.parse_utterance("1 Maggi masala dena", keyterms_enabled=True)
    assert len(res_on["items"]) == 1
    assert res_on["items"][0]["match_confidence"] >= 0.95

    # With keyterms OFF
    res_off = parser.parse_utterance("1 Maggi masala dena", keyterms_enabled=False)
    assert "meghee" in res_off["transcript"]
    assert len(res_off["items"]) == 0 or len(res_off["clarifications_needed"]) > 0

def test_ambiguity_clarification_gate(parser):
    res = parser.parse_utterance("ढाई किलो चावल देना")
    assert len(res["clarifications_needed"]) == 1
    clar = res["clarifications_needed"][0]
    assert clar["family"] == "rice"
    assert "बासमती" in clar["question_hi"]
    assert "सोना मसूरी" in clar["question_hi"]

def test_order_completion_detection(parser):
    res1 = parser.parse_utterance("2 किलो बासमती चावल, बस इतना ही।")
    assert res1["is_order_complete"] is True

    res2 = parser.parse_utterance("1 packet दूध, हो गया।")
    assert res2["is_order_complete"] is True

def test_telephony_mu_law_codec(noise_lab):
    t = np.linspace(0, 1.0, 16000, endpoint=False)
    speech = 0.5 * np.sin(2 * np.pi * 440 * t)
    telephony_audio, target_sr = noise_lab.apply_telephony_codec(speech, orig_sr=16000)
    assert target_sr == 8000
    assert len(telephony_audio) == 8000
    assert np.max(np.abs(telephony_audio)) <= 1.0

def test_item_level_f1_metric(noise_lab):
    gt = [
        {"sku_id": "SKU-001", "qty": 2.0},
        {"sku_id": "SKU-008", "qty": 1.0}
    ]
    pred = [
        {"sku_id": "SKU-001", "qty": 2.0},
        {"sku_id": "SKU-008", "qty": 1.0}
    ]
    stats = noise_lab.calculate_item_level_f1(gt, pred)
    assert stats["item_f1"] == 100.0
    assert stats["true_positives"] == 2

def test_api_endpoints(client):
    # Catalog
    r_cat = client.get("/api/v1/kiranavaani/catalog")
    assert r_cat.status_code == 200
    assert len(r_cat.json()["skus"]) == 35

    # Parse turn
    r_parse = client.post("/api/v1/kiranavaani/parse-turn", json={
        "utterance": "2 किलो बासमती चावल, 1 Maggi masala, बस इतना ही",
        "prisma_version": "prisma-v3.0",
        "keyterms_enabled": True
    })
    assert r_parse.status_code == 200
    assert len(r_parse.json()["items"]) == 2
    assert r_parse.json()["total_inr"] == 204.0

    # Resolve clarification
    r_res = client.post("/api/v1/kiranavaani/resolve-clarification", json={
        "chosen_sku_id": "SKU-002",
        "qty": 2.5,
        "current_cart": []
    })
    assert r_res.status_code == 200
    assert r_res.json()["total_inr"] == 237.5
