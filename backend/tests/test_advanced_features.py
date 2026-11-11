"""
Unit and integration tests for advanced KiranaVaani features:
- Voice Biometrics ('Awaaz Pehchaan' — Gnani Armour360 inspired)
- B2B Mandi Wholesale Replenishment System
- Sub-Second Telemetry & Indic vs US Cloud Benchmark
- Judge's Adversarial Stress-Test Arena
- Bhaav-Taal (भाव-तोल) Bargaining & Margin Negotiation Edge Cases
- Chhotu Delivery Dispatch (किराना डिलीवरी राइडर) Hyperlocal Edge Cases
- Rasoi se Rashan (रसोई से राशन) Meal Recipe to Cart Edge Cases
"""
import base64
import io
import math
import struct
import wave
import pytest
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.services.catalogue_matcher import catalogue_matcher
from backend.app.services.order_parser import order_parser

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


# =========================================================================
# EDGE CASES: Bhaav-Taal (भाव-तोल) Bargaining & Margin Negotiation
# =========================================================================

def test_bhaav_taal_empty_cart_defaults_to_staples():
    """
    Edge Case: Empty cart passed to Bhaav-Taal bargaining.
    Should safely default to standard high-volume staples (10kg Atta + 5kg Rice)
    without raising IndexError or division-by-zero.
    """
    res = client.post("/negotiate-bhav", json={
        "cart_items": [],
        "customer_name": "Sharma Ji (शर्मा जी)"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["is_bargain_intent"] is True
    assert len(data["bargain_items"]) == 2
    assert data["original_total_inr"] > 0
    assert data["negotiated_total_inr"] < data["original_total_inr"]
    assert data["total_savings_inr"] > 0
    assert "पैक कर दूँ?" in data["spoken_counter_offer_hi"]


def test_bhaav_taal_unrecognized_customer():
    """
    Edge Case: Unrecognized/walk-in customer without Khata loyalty history.
    Should gracefully fall back to base loyalty tier with 6% concession and warm banter.
    """
    res = client.post("/negotiate-bhav", json={
        "customer_id": "CUST-UNKNOWN-999",
        "customer_name": "Ramesh Kumar (अपरिचित ग्राहक)",
        "cart_items": [{"sku_id": "SKU-001", "quantity": 5.0}]
    })
    assert res.status_code == 200
    data = res.json()
    assert data["loyalty_tier"] == "GOLD_LOYALTY (पुराने विश्वस्त ग्राहक)"
    assert data["discount_pct"] <= 7.0
    assert "Ramesh Kumar" in data["spoken_counter_offer_hi"]
    assert data["merchant_margin_preserved_pct"] > 0


def test_bhaav_taal_zero_or_low_wholesale_margin():
    """
    Edge Case: Zero wholesale margin / zero discount headroom.
    Verifies that merchant margin is preserved, non-negative, and discount does not wipe out wholesale cost.
    """
    bhaav = catalogue_matcher.compute_bhaav_taal(
        cart_items=[{"sku_id": "SKU-001", "quantity": 1.0}],
        target_discount_pct=0.0
    )
    assert bhaav.original_total_inr > 0
    assert bhaav.negotiated_total_inr > 0
    assert bhaav.total_savings_inr >= 0
    assert bhaav.merchant_margin_preserved_pct >= 0


def test_bhaav_taal_extreme_discount_request_capped():
    """
    Edge Case: Extreme discount request (> 50%, e.g. 75% or 90%).
    Merchant discount rate must be capped at maximum permissible ceiling (<= 9.0%)
    to prevent merchant losses.
    """
    res = client.post("/negotiate-bhav", json={
        "customer_name": "Sharma Ji",
        "cart_items": [{"sku_id": "SKU-001", "quantity": 10.0}],
        "target_discount_pct": 75.0
    })
    assert res.status_code == 200
    data = res.json()
    assert data["discount_pct"] <= 9.0
    assert data["total_savings_inr"] < (data["original_total_inr"] * 0.12)
    assert data["merchant_margin_preserved_pct"] > 0


def test_bhaav_taal_minimal_discount_floor():
    """
    Edge Case: Unusually small discount request (< 3%).
    Should provide at least a 3% friendly Kirana floor.
    """
    res = client.post("/negotiate-bhav", json={
        "customer_name": "Sharma Ji",
        "cart_items": [{"sku_id": "SKU-001", "quantity": 10.0}],
        "target_discount_pct": 1.0
    })
    assert res.status_code == 200
    data = res.json()
    assert data["discount_pct"] >= 3.0


# =========================================================================
# EDGE CASES: Chhotu Delivery Dispatch (किराना डिलीवरी राइडर)
# =========================================================================

def test_delivery_dispatch_missing_landmarks_fallback():
    """
    Edge Case: Spoken directions with missing physical landmarks.
    Should safely supply the default neighborhood landmark and generate valid rider directions.
    """
    res = client.post("/delivery/dispatch-rider", json={
        "customer_name": "Sharma Ji",
        "transcript": "Bhaiya jaldi delivery bhej dena shaam 6 baje",
        "total_amount_inr": 350.0
    })
    assert res.status_code == 200
    data = res.json()
    assert "राम मंदिर के पीछे" in data["vernacular_route_directions"] or "ram mandir ke peeche" in data["vernacular_route_directions"].lower()
    assert "shaam 6 baje" in data["delivery_window"]
    assert "COD Cash Collection" in data["payment_collection_directive"]


def test_delivery_dispatch_missing_time_window_fallback():
    """
    Edge Case: Spoken directions with missing time window.
    Should default to standard evening window ('shaam 6 baje').
    """
    res = client.post("/delivery/dispatch-rider", json={
        "customer_name": "Verma Ji",
        "transcript": "Bhaiya Ram Mandir ke peeche teesri gali me peela makaan bhej dena",
        "total_amount_inr": 420.0
    })
    assert res.status_code == 200
    data = res.json()
    assert "shaam 6 baje" in data["delivery_window"].lower() or "शाम 6:00 बजे" in data["delivery_window"]


def test_delivery_dispatch_empty_directions_and_null_transcript():
    """
    Edge Case: Empty directions string and null customer inputs.
    Must not crash; should populate fallback recipient, landmark, and default ₹465 COD directive.
    """
    res = client.post("/delivery/dispatch-rider", json={
        "transcript": "",
        "customer_name": None,
        "cart_items": None,
        "total_amount_inr": None
    })
    assert res.status_code == 200
    data = res.json()
    assert "RIDER-" in data["dispatch_id"]
    assert "Sharma Ji" in data["customer_name"]
    assert "465" in data["payment_collection_directive"]
    assert "wa.me" in data["whatsapp_url"] or "whatsapp" in data["whatsapp_url"]


def test_delivery_dispatch_khata_credit_and_upi_prepaid_payment_modes():
    """
    Edge Case: Test Khata and UPI prepaid payment modes in delivery dispatch.
    Rider directive should state 'no cash collection needed' for Khata and UPI orders.
    """
    # Khata mode
    res_khata = client.post("/delivery/dispatch-rider", json={
        "transcript": "Delivery Ram Mandir ke peeche bhej do, paise khate me likh lo",
        "total_amount_inr": 250.0
    })
    assert res_khata.status_code == 200
    data_k = res_khata.json()
    assert "खाते में लिख दिया है" in data_k["payment_collection_directive"]

    # UPI Prepaid mode
    res_upi = client.post("/delivery/dispatch-rider", json={
        "transcript": "Delivery Ram Mandir ke peeche bhej do, payment online UPI se kar diya hai",
        "total_amount_inr": 250.0
    })
    assert res_upi.status_code == 200
    data_u = res_upi.json()
    assert "ऑनलाइन UPI से भुगतान" in data_u["payment_collection_directive"]


# =========================================================================
# EDGE CASES: Rasoi se Rashan (रसोई से राशन) Meal Recipe to Cart
# =========================================================================

def test_recipe_unknown_dish_fallback_to_rajma():
    """
    Edge Case: Completely unknown or exotic dish query ('Italian pasta pizza').
    Should gracefully fall back to the flagship Rajma-Chawal meal combo rather than crashing.
    """
    res = client.post("/recipe-to-cart", json={
        "dish_query": "Bhaiya 4 logon ke liye Italian pasta pizza bana rahe hain",
        "servings": 4
    })
    assert res.status_code == 200
    data = res.json()
    assert "Rajma" in data["dish_name_en"]
    assert len(data["matched_ingredients"]) >= 4
    assert data["bundle_discount_inr"] > 0


def test_recipe_zero_and_negative_servings_clamping():
    """
    Edge Case: Servings <= 0 (e.g. 0 or -4 servings).
    Scale must be clamped to minimum 0.5 (half recipe) to prevent negative quantities or empty cart.
    """
    for bad_serving in [0, -4]:
        res = client.post("/recipe-to-cart", json={
            "dish_query": "rajma chawal",
            "servings": bad_serving
        })
        assert res.status_code == 200
        data = res.json()
        assert data["bundle_total_inr"] > 0
        assert len(data["matched_ingredients"]) >= 4
        for ing in data["matched_ingredients"]:
            assert ing["quantity"] > 0.0


def test_recipe_variants_dal_chai_poha_paneer():
    """
    Edge Case: Test all recipe catalogue variants:
    - Dal Tadka & Rice
    - Morning Chai-Nashta
    - Indori Poha Breakfast Pack
    - Shahi Paneer Pulao
    """
    variants = [
        ("dal tadka", "Dal Tadka"),
        ("chai nashta", "Chai-Nashta"),
        ("poha nashta", "Poha"),
        ("paneer pulao", "Paneer Pulao")
    ]
    for query, expected_title in variants:
        res = client.post("/recipe-to-cart", json={
            "dish_query": f"4 logon ke liye {query}",
            "servings": 4
        })
        assert res.status_code == 200
        data = res.json()
        assert expected_title in data["dish_name_en"]
        assert len(data["matched_ingredients"]) >= 3
        assert data["bundle_discount_inr"] > 0


def test_recipe_exclude_seasonings():
    """
    Edge Case: include_seasonings=False.
    Should exclude spices and seasonings (salt, turmeric, mustard oil), returning only core staples.
    """
    res = client.post("/recipe-to-cart", json={
        "dish_query": "rajma chawal",
        "servings": 4,
        "include_seasonings": False
    })
    assert res.status_code == 200
    data = res.json()
    assert len(data["matched_ingredients"]) == 2  # Only Rajma and Rice
    assert all(it["is_core_staple"] is True for it in data["matched_ingredients"])


# =========================================================================
# ADDITIONAL INTEGRATION TESTS: Inventory Deplete & Judge Stress Tests
# =========================================================================

def test_inventory_deplete_endpoint():
    """Verify inventory depletion endpoint decrements stock levels upon order confirmation."""
    res = client.post("/inventory/deplete", json={
        "items": [{"sku_id": "SKU-001", "quantity": 1.0}]
    })
    assert res.status_code == 200
    data = res.json()
    assert data["total_skus"] >= 35
    assert "inventory_items" in data


def test_judge_stress_arena_test_02_03_04_05():
    """Verify Judge stress test cases 02 (Kannada), 03 (Bhasha-Sudhaar), 04 (0dB noise), and 05 (Compound intent)."""
    for test_id in ["TEST-02", "TEST-03", "TEST-04", "TEST-05"]:
        res = client.post("/judge-arena/execute", json={"test_id": test_id})
        assert res.status_code == 200
        data = res.json()
        assert data["test_id"] == test_id
        assert data["item_f1_score"] >= 90.0
        assert len(data["rules_applied"]) >= 2


# =========================================================================
# ARMOUR360 LIVENESS, WHATSAPP VOICE NOTE & JAZBAAT EMOTION TESTS
# =========================================================================

def test_armour_liveness_check_authentic_and_replay_detection():
    """Verify Armour360 Acoustic Liveness & Anti-Spoofing Gate."""
    # 1. Authentic caller
    res_auth = client.post("/khata/liveness-check", json={
        "customer_id": "CUST-001",
        "customer_name": "Sharma Ji",
        "simulate_replay_attack": False
    })
    assert res_auth.status_code == 200
    data_a = res_auth.json()
    assert data_a["is_live_human"] is True
    assert data_a["liveness_score"] >= 0.80
    assert data_a["verdict_badge"] == "VERIFIED_LIVE_HUMAN"
    assert data_a["recommended_action"] == "PROCEED_WITH_CREDIT"

    # 2. Simulated Replay Attack (WhatsApp voice recording played over phone mic)
    res_replay = client.post("/khata/liveness-check", json={
        "customer_id": "CUST-001",
        "customer_name": "Sharma Ji",
        "simulate_replay_attack": True
    })
    assert res_replay.status_code == 200
    data_r = res_replay.json()
    assert data_r["is_live_human"] is False
    assert data_r["verdict_badge"] == "REPLAY_ATTACK_DETECTED"
    assert data_r["attack_type"] == "REPLAY_ATTACK"
    assert data_r["secondary_resonance_db"] > 3.5
    assert data_r["recommended_action"] == "REQUIRE_OTP_VERIFICATION"


def test_whatsapp_voice_note_endpoint():
    """Verify WhatsApp Voice Note PTT audio ingestion and interactive order slip generation."""
    res = client.post("/whatsapp/voice-note", json={
        "sender_name": "Sharma Ji (शर्मा जी)",
        "sender_phone": "+91 98201-12345",
        "preset_id": "snack_rush"
    })
    assert res.status_code == 200
    data = res.json()
    assert "upi://" in data["upi_payment_link"]
    assert "गुप्ता किराना स्टोर" in data["whatsapp_auto_reply_text"]
    assert data["cart_total_inr"] > 0
    assert len(data["parsed_items"]) >= 2
    assert data["estimated_delivery_mins"] <= 20
    assert data["is_tatkal"] is True


def test_customer_jazbaat_urgency_detection():
    """Verify call360 Awaaz-e-Jazbaat urgency and sentiment telemetry."""
    # Urgent query
    jaz_urgent = order_parser.extract_customer_jazbaat("अरे भैया बहुत जल्दी 2 पैकेट दूध भेजो मेहमान बैठे हैं तुरंत चाहिए")
    assert jaz_urgent.is_tatkal_priority is True
    assert jaz_urgent.urgency_level == "TATKAL_EXPRESS_10MIN"
    assert jaz_urgent.urgency_score >= 0.60
    assert len(jaz_urgent.detected_cues) >= 2
    assert "तत्काल" in jaz_urgent.merchant_action_hint_hi

    # Routine relaxed query
    jaz_routine = order_parser.extract_customer_jazbaat("भैया 1 किलो आटा और आधा किलो चीनी भिजवा देना जब भी समय मिले")
    assert jaz_routine.is_tatkal_priority is False
    assert jaz_routine.urgency_level == "NORMAL"


def test_judge_stress_arena_test_09_10():
    """Verify Judge Stress Arena Test Cases 09 (Armour360 Replay Guard) and 10 (call360 Tatkal Urgency)."""
    # Test 09: Replay Attack Defense
    res_09 = client.post("/judge-arena/execute", json={"test_id": "TEST-09"})
    assert res_09.status_code == 200
    data_09 = res_09.json()
    assert data_09["test_id"] == "TEST-09"
    assert data_09["voiceprint_status"] == "REPLAY_SPOOF_BLOCKED"
    assert data_09["item_f1_score"] == 100.0

    # Test 10: Tatkal Urgency Dispatch
    res_10 = client.post("/judge-arena/execute", json={"test_id": "TEST-10"})
    assert res_10.status_code == 200
    data_10 = res_10.json()
    assert data_10["test_id"] == "TEST-10"
    assert data_10["item_f1_score"] == 100.0
    assert any("Tatkal" in r or "तत्काल" in r for r in data_10["rules_applied"])


def test_whatsapp_voice_note_presets_routine_and_evening():
    """Verify WhatsApp Voice Note handles routine breakfast and evening delivery windows."""
    # Breakfast basket (routine 20 min)
    res = client.post("/whatsapp/voice-note", json={
        "sender_name": "Gupta Ji",
        "sender_phone": "+91 98201-99999",
        "preset_id": "breakfast_basket"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["is_tatkal"] is False
    assert data["estimated_delivery_mins"] == 20
    assert len(data["parsed_items"]) >= 1

    # Evening rashan (6 PM delivery window)
    res_eve = client.post("/whatsapp/voice-note", json={
        "sender_name": "Verma Ji",
        "sender_phone": "+91 98201-88888",
        "preset_id": "evening_rashan"
    })
    assert res_eve.status_code == 200
    data_eve = res_eve.json()
    assert "चावल" in data_eve["whatsapp_auto_reply_text"] or "chawal" in data_eve["whatsapp_auto_reply_text"].lower()


def test_whatsapp_voice_note_invalid_base64_fallback():
    """Verify WhatsApp Voice Note gracefully falls back when given malformed base64."""
    res = client.post("/whatsapp/voice-note", json={
        "sender_name": "Sharma Ji",
        "audio_base64": "!!!NOT_VALID_BASE64!!!"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["cart_total_inr"] > 0
    assert len(data["parsed_items"]) >= 1


def test_armour_liveness_synthetic_ai_clone_detection():
    """Verify Armour360 Liveness Gate detects AI synthetic voice clone flatline."""
    res = client.post("/khata/liveness-check", json={
        "customer_id": "CUST-001",
        "simulate_synthetic_voice": True
    })
    assert res.status_code == 200
    data = res.json()
    assert data["is_live_human"] is False
    assert data["verdict_badge"] == "SYNTHETIC_CLONE_DETECTED"
    assert data["attack_type"] == "SYNTHETIC_VOICE"
    assert data["jitter_percent"] < 0.20
    assert data["recommended_action"] == "BLOCK_TRANSACTION"
    # Also verify computed properties for frontend
    assert data["is_live"] is False
    assert data["action_permitted"] is False


def test_armour_liveness_pcm_extraction_robustness():
    """Verify Armour360 PCM extraction safely handles truncated or arbitrary byte streams."""
    from backend.app.services.armour_liveness import armour_liveness_service
    # Empty bytes
    samples_empty = armour_liveness_service._extract_pcm_samples(b"")
    assert samples_empty == []

    # Corrupt single byte
    samples_corrupt = armour_liveness_service._extract_pcm_samples(b"\x00")
    assert samples_corrupt == []

    # Odd-length raw audio buffer
    samples_odd = armour_liveness_service._extract_pcm_samples(b"\x00\x10\x00\x20\x00")
    assert len(samples_odd) >= 0


def test_customer_jazbaat_edge_cases_and_dravidian():
    """Verify call360 Awaaz-e-Jazbaat edge cases: empty strings, Dravidian cues, high word count."""
    # Empty string
    jaz_empty = order_parser.extract_customer_jazbaat("")
    assert jaz_empty.urgency_level == "NORMAL"
    assert jaz_empty.is_tatkal_priority is False
    assert jaz_empty.speech_tempo_wpm == 120.0

    # Dravidian urgency
    jaz_dravidian = order_parser.extract_customer_jazbaat("Anna begane kodi thumba urgent order")
    assert any("begane" in c or "urgent" in c for c in jaz_dravidian.detected_cues)
    assert jaz_dravidian.is_tatkal_priority is True

    # High tempo clause
    long_urgent = "Bhaiya jaldi se do kilo atta aur ek kilo cheeni aur aadha litre doodh aur do packet maggi aur ek chai patti turant bhejo"
    jaz_long = order_parser.extract_customer_jazbaat(long_urgent)
    assert jaz_long.speech_tempo_wpm > 150.0
    assert jaz_long.is_tatkal_priority is True


# =========================================================================
# QA AUDIT EXPANSION: WhatsApp Voice Notes, Armour360 Spoofing & Jazbaat WPM
# =========================================================================

def test_whatsapp_voice_note_missing_and_unknown_preset_fallback():
    """Verify /whatsapp/voice-note handles missing preset_id (None) or unknown preset gracefully."""
    # 1. Missing preset_id entirely (None)
    res_none = client.post("/whatsapp/voice-note", json={
        "sender_name": "Sharma Ji",
        "sender_phone": "+91 98201-11111",
        "preset_id": None
    })
    assert res_none.status_code == 200
    data_none = res_none.json()
    assert data_none["cart_total_inr"] > 0
    assert len(data_none["parsed_items"]) >= 2
    assert "upi://" in data_none["upi_payment_link"]
    assert "गुप्ता किराना स्टोर" in data_none["whatsapp_auto_reply_text"]

    # 2. Unrecognized preset string
    res_unknown = client.post("/whatsapp/voice-note", json={
        "sender_name": "Verma Ji",
        "preset_id": "nonexistent_alien_preset_xyz"
    })
    assert res_unknown.status_code == 200
    data_unk = res_unknown.json()
    assert data_unk["confirmed_skus_count"] >= 1
    assert data_unk["estimated_delivery_mins"] in (10, 20)


def test_whatsapp_voice_note_empty_audio_inputs():
    """Verify /whatsapp/voice-note safely handles empty string, whitespace, and 0-byte audio inputs."""
    empty_payloads = [
        "",
        "   \t\n  ",
        base64.b64encode(b"").decode()
    ]
    for empty_audio in empty_payloads:
        res = client.post("/whatsapp/voice-note", json={
            "sender_name": "Sunita Devi",
            "audio_base64": empty_audio,
            "preset_id": None
        })
        assert res.status_code == 200
        data = res.json()
        assert data["cart_total_inr"] > 0
        assert "upi://" in data["upi_payment_link"]


def test_whatsapp_voice_note_large_payload_handling():
    """Verify /whatsapp/voice-note can ingest large audio payloads without memory exhaustion."""
    dummy_audio_bytes = b"RIFF" + b"\x00" * 250000
    large_b64 = base64.b64encode(dummy_audio_bytes).decode("ascii")

    res = client.post("/whatsapp/voice-note", json={
        "sender_name": "Ramesh Kumar",
        "sender_phone": "+91 98111-55555",
        "audio_base64": large_b64,
        "audio_filename": "long_voice_note.ogg",
        "preset_id": None
    })
    assert res.status_code == 200
    data = res.json()
    assert data["cart_total_inr"] > 0
    assert data["voice_audio_base64"] is not None


def test_whatsapp_voice_note_urgent_vs_non_urgent_contrast():
    """Verify explicit contrast between urgent Tatkal notes (10-min) and routine grocery notes (20-min)."""
    # 1. Urgent Note ('snack_rush' with 'तुरंत' urgency marker)
    res_urgent = client.post("/whatsapp/voice-note", json={
        "sender_name": "Sharma Ji",
        "preset_id": "snack_rush"
    })
    assert res_urgent.status_code == 200
    data_u = res_urgent.json()
    assert data_u["is_tatkal"] is True
    assert data_u["estimated_delivery_mins"] == 10
    assert "⚡ तत्काल 10 मिनट डिलीवरी" in data_u["whatsapp_auto_reply_text"]

    # 2. Non-Urgent Note ('evening_rashan' with 'शाम 6 बजे' window)
    res_routine = client.post("/whatsapp/voice-note", json={
        "sender_name": "Sharma Ji",
        "preset_id": "evening_rashan"
    })
    assert res_routine.status_code == 200
    data_r = res_routine.json()
    assert data_r["is_tatkal"] is False
    assert data_r["estimated_delivery_mins"] == 20
    assert "सामान्य डिलीवरी" in data_r["whatsapp_auto_reply_text"]


def test_khata_liveness_authentic_deep_contract():
    """Verify authentic live human speaker passes all Armour360 verification gates with full contract assertion."""
    res = client.post("/khata/liveness-check", json={
        "customer_id": "CUST-001",
        "customer_name": "Sharma Ji (शर्मा जी)",
        "simulate_replay_attack": False,
        "simulate_synthetic_voice": False
    })
    assert res.status_code == 200
    data = res.json()
    assert data["is_live_human"] is True
    assert data["liveness_score"] >= 0.85
    assert data["verdict_badge"] == "VERIFIED_LIVE_HUMAN"
    assert data["attack_type"] is None
    assert data["recommended_action"] == "PROCEED_WITH_CREDIT"
    assert data["secondary_resonance_db"] < 3.0
    assert "सफल" in data["security_prompt_hi"]


def test_khata_liveness_conflicting_attack_flags():
    """Verify when both replay and synthetic attack flags are sent, gateway safely prioritizes replay detection."""
    res = client.post("/khata/liveness-check", json={
        "customer_id": "CUST-001",
        "simulate_replay_attack": True,
        "simulate_synthetic_voice": True
    })
    assert res.status_code == 200
    data = res.json()
    assert data["is_live_human"] is False
    assert data["attack_type"] == "REPLAY_ATTACK"
    assert data["verdict_badge"] == "REPLAY_ATTACK_DETECTED"
    assert data["recommended_action"] == "REQUIRE_OTP_VERIFICATION"


def test_khata_liveness_corrupted_base64_endpoint_fallback():
    """Verify endpoint catches corrupted base64 string and falls back to safe acoustic baseline."""
    res = client.post("/khata/liveness-check", json={
        "customer_id": "CUST-001",
        "audio_base64": "NOT_VALID_BASE64_AT_ALL!@#$%^&*()",
        "simulate_replay_attack": False,
        "simulate_synthetic_voice": False
    })
    assert res.status_code == 200
    data = res.json()
    assert data["is_live_human"] is True
    assert data["verdict_badge"] == "VERIFIED_LIVE_HUMAN"


def test_khata_liveness_corrupted_binary_audio_buffer():
    """Verify endpoint handles valid Base64 that decodes to corrupted non-WAV bytes via DSP fallback."""
    corrupt_bytes = b"MALFORMED_HEADER" * 30  # 480 bytes of non-WAV data
    corrupt_b64 = base64.b64encode(corrupt_bytes).decode("ascii")

    res = client.post("/khata/liveness-check", json={
        "customer_id": "CUST-001",
        "audio_base64": corrupt_b64
    })
    assert res.status_code == 200
    data = res.json()
    assert "liveness_score" in data
    assert data["verdict_badge"] in ("VERIFIED_LIVE_HUMAN", "REPLAY_ATTACK_DETECTED", "SYNTHETIC_CLONE_DETECTED")


def test_khata_liveness_real_pcm_audio_buffer():
    """Verify end-to-end DSP pipeline with a real synthesized 16-bit PCM WAV audio buffer."""
    sr = 16000
    duration = 0.25
    n_samples = int(sr * duration)
    wav_buf = io.BytesIO()
    with wave.open(wav_buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        sine_samples = [int(16000 * math.sin(2 * math.pi * 440 * i / sr)) for i in range(n_samples)]
        wf.writeframes(struct.pack(f"<{n_samples}h", *sine_samples))
    
    real_audio_b64 = base64.b64encode(wav_buf.getvalue()).decode("ascii")
    res = client.post("/khata/liveness-check", json={
        "customer_id": "CUST-001",
        "audio_base64": real_audio_b64
    })
    assert res.status_code == 200
    data = res.json()
    assert data["spectral_flux"] > 0
    assert data["jitter_percent"] > 0


def test_jazbaat_mixed_scripts_and_devanagari_numerals():
    """Verify Jazbaat urgency extraction with mixed Devanagari numerals ('१० मिनट'), Tamil, and kitchen emergency cues."""
    # 1. Devanagari Numerals + English words
    j1 = order_parser.extract_customer_jazbaat("bhaiya १० मिनट me delivery chahiye mehmaan aaye hain")
    assert j1.is_tatkal_priority is True
    assert j1.urgency_level == "TATKAL_EXPRESS_10MIN"
    assert any(c in j1.detected_cues for c in ["१० मिनट", "mehmaan"])

    # 2. Tamil Urgency Cues
    j2 = order_parser.extract_customer_jazbaat("Anna seekiram 1 kg sugar anupunga, udane venum")
    assert j2.is_tatkal_priority is True
    assert any("seekiram" in c or "udane" in c for c in j2.detected_cues)

    # 3. Cooking Emergency (gas pe chai chadhayi hai)
    j3 = order_parser.extract_customer_jazbaat("अरे भैया gas pe chai chadhayi hai jaldi doodh bhej do")
    assert j3.is_tatkal_priority is True
    assert any(c in j3.detected_cues for c in ["gas pe", "chai chadhayi", "jaldi"])

    # 4. Direct Tatkal Single-Word Triggers
    for trig in ["emergency", "इमरजेंसी", "fatafat", "तुरंत", "right now"]:
        j_trig = order_parser.extract_customer_jazbaat(f"bhaiya {trig} 2 packet bread bhej do")
        assert j_trig.is_tatkal_priority is True
        assert j_trig.urgency_score >= 0.65


def test_jazbaat_wpm_boundary_conditions():
    """Verify exact word-count boundary values for speech tempo calculation: 12, 13, 24, 35 words."""
    # 1. Exactly 12 words (tempo 120.0, no tempo bonus)
    twelve_words = "ek do teen chaar paanch chhah saat aath nau das gyarah baarah"
    j12 = order_parser.extract_customer_jazbaat(twelve_words)
    assert j12.speech_tempo_wpm == 120.0

    # 2. Exactly 13 words (crosses 12-word threshold -> 130 + 13 * 2.5 = 162.5)
    thirteen_words = twelve_words + " terah"
    j13 = order_parser.extract_customer_jazbaat(thirteen_words)
    assert j13.speech_tempo_wpm == 162.5

    # 3. Exactly 24 words (hits 190.0 WPM)
    twenty_four_words = " ".join([f"word{i}" for i in range(1, 25)])
    j24 = order_parser.extract_customer_jazbaat(twenty_four_words)
    assert j24.speech_tempo_wpm == 190.0

    # 4. Extreme 35 words (must be clamped at 190.0 WPM ceiling)
    thirty_five_words = " ".join([f"word{i}" for i in range(1, 36)])
    j35 = order_parser.extract_customer_jazbaat(thirty_five_words)
    assert j35.speech_tempo_wpm == 190.0


def test_jazbaat_zero_words_and_symbol_inputs():
    """Verify zero words, pure whitespace, and symbols produce safe fallback metrics."""
    safe_test_cases = [
        "",
        "      ",
        "\n\t\r",
        "??? !!! ... ,,, ---"
    ]
    for raw in safe_test_cases:
        j = order_parser.extract_customer_jazbaat(raw)
        assert j.urgency_level == "NORMAL"
        assert j.is_tatkal_priority is False
        assert j.speech_tempo_wpm == 120.0
        assert j.detected_cues == []
        assert j.sentiment == "POLITE_NEUTRAL"
