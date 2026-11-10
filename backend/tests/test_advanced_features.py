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


def test_voiceprint_verification_unenrolled_404():
    """Verify unenrolled customer ID returns HTTP 404 rather than false authentication."""
    res = client.post("/khata/verify-voiceprint", json={
        "customer_id": "CUST-UNKNOWN-999",
        "caller_phone": "+91 99999-99999",
        "test_imposter_mode": False
    })
    assert res.status_code == 404
    assert "no enrolled voiceprint profile" in res.json()["detail"]


def test_voiceprint_verification_aliases():
    """Verify Khata ID alias '#42' and '42' correctly resolve to Sharma Ji's biometric profile."""
    for alias in ["#42", "42"]:
        res = client.post("/khata/verify-voiceprint", json={
            "customer_id": alias,
            "caller_phone": "+91 98111-23456",
            "test_imposter_mode": False
        })
        assert res.status_code == 200
        data = res.json()
        assert data["verified"] is True
        assert "Sharma Ji" in data["customer_name"]


def test_mandi_wholesale_order_invalid_sku_404():
    """Verify attempting to order a non-existent SKU returns HTTP 404."""
    res = client.post("/inventory/mandi-order", json={
        "sku_id": "SKU-NONEXISTENT",
        "reorder_quantity": 25.0
    })
    assert res.status_code == 404
    assert "not found in catalogue" in res.json()["detail"]


def test_mandi_wholesale_order_fallback_phone():
    """Verify mandi order without custom phone uses store fallback phone safely."""
    res = client.post("/inventory/mandi-order", json={
        "sku_id": "SKU-001",
        "reorder_quantity": 20.0,
        "wholesaler_phone": None
    })
    assert res.status_code == 200
    data = res.json()
    assert "wa.me" in data["whatsapp_url"]


def test_mandi_order_quantity_validation():
    """Verify invalid reorder quantities (e.g. <= 0 or > 5000) are rejected with HTTP 422."""
    res = client.post("/inventory/mandi-order", json={
        "sku_id": "SKU-001",
        "reorder_quantity": -5.0
    })
    assert res.status_code == 422


def test_judge_stress_arena_invalid_test_id_404():
    """Verify executing a non-existent test case returns HTTP 404."""
    res = client.post("/judge-arena/execute", json={"test_id": "TEST-INVALID-99"})
    assert res.status_code == 404
    assert "not found" in res.json()["detail"]


def test_bhaav_taal_bargaining_endpoint():
    """Verify Bhaav-Taal voice bargaining calculates dynamic wholesale margin and counter-offer."""
    res = client.post("/negotiate-bhav", json={
        "customer_name": "Sharma Ji (शर्मा जी)",
        "cart_items": [
            {"sku_id": "SKU-001", "quantity": 10.0},
            {"sku_id": "SKU-002", "quantity": 5.0}
        ],
        "target_discount_pct": 5.0
    })
    assert res.status_code == 200
    data = res.json()
    assert data["is_bargain_intent"] is True
    assert data["original_total_inr"] > data["negotiated_total_inr"]
    assert data["total_savings_inr"] > 0
    assert "शर्मा जी" in data["spoken_counter_offer_hi"]
    assert len(data["bargain_items"]) == 2
    assert data["merchant_margin_preserved_pct"] > 0


def test_delivery_rider_dispatch_endpoint():
    """Verify Chhotu Delivery Landmark dispatch generates vernacular directions and rider voice note."""
    res = client.post("/delivery/dispatch-rider", json={
        "customer_name": "Sharma Ji",
        "transcript": "Bhaiya delivery Ram Mandir ke peeche, teesri gali me peela makaan, second floor pe bhej dena shaam 6 baje",
        "total_amount_inr": 500.0,
        "cart_items": [{"sku_id": "SKU-001", "quantity": 2.0}]
    })
    assert res.status_code == 200
    data = res.json()
    assert "RIDER-" in data["dispatch_id"]
    assert ("ram mandir ke peeche" in data["vernacular_route_directions"].lower() or "राम मंदिर के पीछे" in data["vernacular_route_directions"])
    assert "shaam 6 baje" in data["delivery_window"]
    assert "whatsapp_url" in data
    assert "Chhotu" in data["rider_name"]
    assert len(data["rider_voice_note_hi"]) > 10


def test_recipe_to_cart_decomposition_endpoint():
    """Verify Rasoi se Rashan meal recipe decomposer extracts constituents with combo discount."""
    res = client.post("/recipe-to-cart", json={
        "dish_query": "4 logon ke liye rajma chawal",
        "servings": 4,
        "include_seasonings": True
    })
    assert res.status_code == 200
    data = res.json()
    assert "Rajma" in data["dish_name_en"]
    assert len(data["matched_ingredients"]) >= 4
    assert data["bundle_discount_inr"] > 0
    assert data["bundle_total_inr"] < data["bundle_subtotal_inr"]
    assert "राजमा" in data["spoken_recipe_prompt_hi"]


def test_judge_stress_arena_test_06_07_08():
    """Verify that newly added Judge Test Cases 06 (Bargaining), 07 (Landmark), and 08 (Recipe) pass."""
    for test_id in ["TEST-06", "TEST-07", "TEST-08"]:
        res = client.post("/judge-arena/execute", json={"test_id": test_id})
        assert res.status_code == 200
        data = res.json()
        assert data["test_id"] == test_id
        assert data["item_f1_score"] == 100.0
        assert len(data["rules_applied"]) >= 2

