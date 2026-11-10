"""
Unit and integration tests for advanced KiranaVaani features:
- Voice Biometrics ('Awaaz Pehchaan' — Gnani Armour360 inspired)
- B2B Mandi Wholesale Replenishment System
- Sub-Second Telemetry & Indic vs US Cloud Benchmark
- Judge's Adversarial Stress-Test Arena
"""
import pytest
from starlette.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_voiceprint_verification_authentic():
    """Verify authentic customer voiceprint verification succeeds with > 90% match."""
    res = client.post("/khata/verify-voiceprint", json={
        "customer_id": "CUST-001",
        "caller_phone": "+91 98111-23456",
        "test_imposter_mode": False
    })
    assert res.status_code == 200
    data = res.json()
    assert data["verified"] is True
    assert data["match_score"] >= 0.90
    assert data["confidence_tier"] == "HIGH_CONFIDENCE_MATCH"
    assert data["khata_debit_permitted"] is True
    assert "Sharma Ji" in data["customer_name"]
    assert "SHA256:" in data["voiceprint_hash"]
    assert data["fundamental_freq_f0_hz"] > 0
    assert data["voice_audio_base64"] is not None


def test_voiceprint_verification_imposter():
    """Verify imposter caller voiceprint fails authentication and blocks Khata debit."""
    res = client.post("/khata/verify-voiceprint", json={
        "customer_id": "CUST-001",
        "caller_phone": "+91 99999-00000",
        "test_imposter_mode": True
    })
    assert res.status_code == 200
    data = res.json()
    assert data["verified"] is False
    assert data["match_score"] < 0.60
    assert data["confidence_tier"] == "IMPOSTER_REJECTED"
    assert data["khata_debit_permitted"] is False
    assert "ALERT" in data["auth_badge_text"]


def test_inventory_status_and_mandi_triggers():
    """Verify inventory status returns stock counts and flags low-stock Mandi restock triggers."""
    res = client.get("/inventory/status")
    assert res.status_code == 200
    data = res.json()
    assert data["total_skus"] >= 35
    assert "inventory_items" in data
    assert len(data["inventory_items"]) >= 35
    assert data["low_stock_count"] >= 0
    if data["reorder_triggers"]:
        trigger = data["reorder_triggers"][0]
        assert trigger["wholesale_rate_inr"] > 0
        assert "Mandi" in trigger["wholesaler_name"]
        assert "whatsapp_po_text" in trigger


def test_mandi_wholesale_order_dispatch():
    """Verify dispatching a B2B wholesale order generates PO, WhatsApp URL, and voice audio."""
    res = client.post("/inventory/mandi-order", json={
        "sku_id": "SKU-001",
        "reorder_quantity": 50.0,
        "wholesaler_name": "Radhe Shyam Agro Mandi Wholesalers",
        "wholesaler_phone": "+91 98765-43210"
    })
    assert res.status_code == 200
    data = res.json()
    assert "MND-PO-" in data["po_id"]
    assert data["quantity"] == 50.0
    assert data["wholesale_rate_inr"] > 0
    assert data["total_cost_inr"] > 0
    assert "wa.me" in data["whatsapp_url"]
    assert data["voice_audio_base64"] is not None


def test_telemetry_benchmark_endpoint():
    """Verify sub-second telemetry benchmark returns pipeline latency and US cloud comparisons."""
    res = client.get("/benchmark/telemetry-compare")
    assert res.status_code == 200
    data = res.json()
    assert data["pipeline_total_latency_ms"] < 600.0  # Must be sub-second conversational
    assert len(data["stages"]) == 5
    assert len(data["comparisons"]) >= 4
    assert data["indic_fraction_accuracy_pct"] > 90.0
    assert data["cost_per_order_inr"] < 0.20
    assert data["savings_pct"] > 80.0


def test_judge_stress_arena_listing_and_execution():
    """Verify judge stress tests list and execute with full Item-F1 and telemetry rules."""
    res = client.get("/judge-arena/tests")
    assert res.status_code == 200
    tests = res.json()
    assert len(tests) >= 5

    # Execute TEST-01 (Colloquial fractions)
    exec_res = client.post("/judge-arena/execute", json={"test_id": "TEST-01"})
    assert exec_res.status_code == 200
    exec_data = exec_res.json()
    assert exec_data["test_id"] == "TEST-01"
    assert exec_data["item_f1_score"] == 100.0
    assert len(exec_data["rules_applied"]) >= 3
    assert exec_data["latency_ms"] > 0
