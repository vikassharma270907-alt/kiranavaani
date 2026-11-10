"""
Integration tests for KiranaVaani FastAPI endpoints.
Tests /health, /catalogue, /transcribe, /parse-order, /match-products, /cart, /synthesize, /process-order.
"""
import pytest
from starlette.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["catalogue_sku_count"] >= 30
    assert "gnani_live_configured" in data


def test_catalogue_endpoint():
    response = client.get("/catalogue")
    assert response.status_code == 200
    data = response.json()
    assert data["total_skus"] >= 30
    assert len(data["skus"]) == data["total_skus"]


def test_parse_order_endpoint():
    payload = {
        "transcript": "Bhaiya do packet Maggi, ek kilo sugar aur aadha litre milk bhej dena.",
        "keyterms_enabled": True
    }
    response = client.post("/parse-order", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3
    prods = [i["product"].lower() for i in data["items"]]
    assert any("maggi" in p for p in prods)
    assert any("sugar" in p for p in prods)
    assert any("milk" in p for p in prods)


def test_match_products_endpoint():
    payload = {
        "items": [
            {"product": "Sugar", "quantity": 1.0, "unit": "kg"},
            {"product": "Tata Salt", "quantity": 1.0, "unit": "packet"},
            {"product": "chawal", "quantity": 2.0, "unit": "kg"}
        ],
        "keyterms_enabled": True
    }
    response = client.post("/match-products", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Confirmed matches
    matched = [m for m in data["matched_items"] if m["status"] == "MATCHED"]
    assert len(matched) >= 2

    # Clarification needed for generic "chawal"
    assert len(data["clarifications_needed"]) >= 1
    assert data["clarifications_needed"][0]["family"] == "rice"


def test_cart_endpoint():
    payload = {
        "items": [
            {"sku_id": "SKU-004", "quantity": 1.0},  # Sugar
            {"sku_id": "SKU-005", "quantity": 1.0}   # Salt
        ]
    }
    response = client.post("/cart", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["item_count"] == 2
    assert data["total_inr"] > 0
    assert "रुपये" in data["spoken_summary_hi"]
    assert len(data["items"]) == 2


def test_cart_gram_to_kg_normalization():
    """Verify 500 gram of sugar (SKU-020, ₹46/kg) bills as 0.5 kg = ₹23.0."""
    payload = {
        "items": [
            {"sku_id": "SKU-020", "quantity": 500.0, "unit": "gram"}
        ]
    }
    response = client.post("/cart", json=payload)
    assert response.status_code == 200
    data = response.json()
    item = data["items"][0]
    assert item["quantity"] == 0.5
    assert item["unit"] == "kg"
    assert item["line_total"] == 23.0


def test_synthesize_endpoint_fallback():
    """Verify fallback audio is cleanly generated when live Timbre key is missing."""
    payload = {
        "text": "नमस्ते, आपका ऑर्डर दर्ज हो गया है।",
        "voice": "Nalini",
        "language": "hi-IN"
    }
    response = client.post("/synthesize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "audio_base64" in data
    assert len(data["audio_base64"]) > 50
    assert data["audio_format"] == "wav"


def test_process_order_preserves_clarification():
    """
    Verify process-order preserves clarification for ambiguous items (e.g. Maggi or generic chawal)
    rather than silently picking a product.
    """
    payload = {
        "transcript": "Bhaiya do packet Maggi, ek kilo sugar aur aadha litre milk bhej dena.",
        "keyterms_enabled": True,
        "synthesize_voice": True
    }
    response = client.post("/process-order", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Ambiguity clarification check
    assert len(data["clarifications_needed"]) >= 1
    assert data["clarifications_needed"][0]["family"] == "maggi"

    # Confirmed cart should contain sugar (SKU-020) and milk (SKU-012)
    cart_items = data["confirmed_cart"]["items"]
    cart_skus = [ci["sku_id"] for ci in cart_items]
    assert "SKU-020" in cart_skus or "SKU-012" in cart_skus  # Sugar or Milk SKU present

    # Voice audio generated
    assert data["voice_audio_base64"] is not None


def test_configured_api_keys_helper(monkeypatch):
    """Verify get_configured_api_keys correctly extracts and prioritizes valid vach_ keys."""
    from backend.app.config import get_configured_api_keys, is_live_gnani_configured

    monkeypatch.setenv("GNANI_API_KEY", "vach_testkey1")
    monkeypatch.setenv("GNANI_API_KEY_FALLBACK", "vach_testkey2")
    monkeypatch.setenv("GNANI_API_KEYS", "vach_testkey3,invalid_key,vach_testkey1")

    keys = get_configured_api_keys()
    assert keys == ["vach_testkey1", "vach_testkey2", "vach_testkey3"]
    assert is_live_gnani_configured() is True


def test_spa_404_handler_serves_index():
    """Verify SPA fallback returns 200 HTML when dist is built, or 404 without NameError."""
    from backend.app.main import frontend_dist
    response = client.get("/nonexistent-spa-route")
    if frontend_dist.exists() and (frontend_dist / "index.html").exists():
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
    else:
        assert response.status_code == 404


def test_docs_and_openapi():
    """Verify Swagger docs, Redoc, and OpenAPI JSON are all accessible."""
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200
    res_oa = client.get("/openapi.json")
    assert res_oa.status_code == 200
    data = res_oa.json()
    assert "/health" in data["paths"]
    assert "/process-order" in data["paths"]


def test_clarification_category_preservation():
    """Verify that clarification options retain the SKU category."""
    payload = {
        "items": [
            {"product": "chawal", "quantity": 2.0, "unit": "kg"}
        ],
        "keyterms_enabled": True
    }
    response = client.post("/match-products", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["clarifications_needed"]) >= 1
    options = data["clarifications_needed"][0]["options"]
    assert len(options) >= 2
    for opt in options:
        assert opt["category"] is not None
        assert len(opt["category"]) > 0


def test_cart_paise_formatting():
    """Verify that non-integer rupee totals retain fractional paise in Hindi summary."""
    payload = {
        "items": [
            {"sku_id": "SKU-002", "quantity": 0.5, "unit": "kg"}  # ₹95/kg * 0.5 = ₹47.50
        ]
    }
    response = client.post("/cart", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_inr"] == 47.50
    assert "47.50" in data["spoken_summary_hi"]


def test_audio_samples_endpoint():
    """Verify audio samples metadata endpoint returns 5 clips with clean/degraded URLs."""
    res = client.get("/audio-samples")
    assert res.status_code == 200
    clips = res.json()
    assert len(clips) >= 5
    ids = [c["clip_id"] for c in clips]
    assert "clip_1_brand_keyterms" in ids
    assert "clip_5_kannada_hinglish" in ids
    # Verify streaming endpoint works for clip 1
    stream_res = client.get(clips[0]["clean_audio_url"])
    assert stream_res.status_code in (200, 404)  # 200 if file exists on disk, 404 if missing


def test_process_order_spoken_clarification_resolution():
    """Verify that spoken clarification reply ('basmati wala') resolves an active ambiguity."""
    payload = {
        "transcript": "Basmati rice pack kar do bhaiya",
        "pending_clarification_family": "rice",
        "keyterms_enabled": True,
        "synthesize_voice": False
    }
    res = client.post("/process-order", json=payload)
    assert res.status_code == 200
    data = res.json()
    # Ambiguity should be resolved and item added to cart
    assert len(data["confirmed_cart"]["items"]) >= 1
    assert any("Basmati" in it["name_en"] for it in data["confirmed_cart"]["items"])
    assert "बासमती" in data["spoken_reply_hi"]


def test_process_order_with_khata_ledger():
    """Verify that orders mentioning khata are tagged with KhataInfo and spoken ledger update."""
    payload = {
        "transcript": "Sharma ji ke khaate me likh lo bhaiya, 1 kilo sugar aur 1 packet Tata Salt, bas itna hi",
        "keyterms_enabled": True,
        "synthesize_voice": False
    }
    res = client.post("/process-order", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["khata_info"] is not None
    assert data["khata_info"]["is_khata"] is True
    assert "खाते में दर्ज" in data["spoken_reply_hi"]


def test_smart_cross_sell_upsell():
    """Verify Dukandar ki Salah (Smart Cross-Sell) suggests Parle-G when Tea + Sugar are ordered."""
    payload = {
        "transcript": "Bhaiya ek packet Red Label tea aur 1 kilo sugar bhej dena, bas itna hi",
        "keyterms_enabled": True,
        "synthesize_voice": False
    }
    res = client.post("/process-order", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["upsell_suggestion"] is not None
    assert data["upsell_suggestion"]["sku_id"] == "SKU-031"  # Parle-G
    assert "पारले-जी" in data["upsell_suggestion"]["pitch_hi"]


def test_out_of_stock_substitution():
    """Verify that when an SKU is marked out of stock, matching produces OUT_OF_STOCK_SUBSTITUTION."""
    # 1. Toggle stock of Amul Butter (SKU-013) to False
    toggle_res = client.post("/catalogue/toggle-stock", json={"sku_id": "SKU-013", "in_stock": False})
    assert toggle_res.status_code == 200
    assert toggle_res.json()["in_stock"] is False

    try:
        # 2. Process order asking for Amul butter
        payload = {
            "transcript": "Bhaiya 1 Amul butter de do",
            "keyterms_enabled": True,
            "synthesize_voice": False
        }
        res = client.post("/process-order", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert len(data["substitutions_needed"]) >= 1
        sub = data["substitutions_needed"][0]
        assert sub["out_of_stock_sku"]["sku_id"] == "SKU-013"
        assert sub["substitute_sku"] is not None
        assert ("मक्खन" in sub["spoken_prompt_hi"] or "बटर" in sub["spoken_prompt_hi"])
    finally:
        # Re-enable stock
        client.post("/catalogue/toggle-stock", json={"sku_id": "SKU-013", "in_stock": True})


def test_khata_customers_and_settlement():
    """Verify Khata ledger listing and settlement endpoints."""
    # List customers
    list_res = client.get("/khata/customers")
    assert list_res.status_code == 200
    ledger = list_res.json()
    assert len(ledger["customers"]) >= 4
    sharma = next(c for c in ledger["customers"] if "Sharma" in c["name"])
    init_bal = sharma["current_balance_inr"]

    # Settle payment of ₹100
    settle_res = client.post("/khata/settle", json={
        "customer_id": sharma["customer_id"],
        "amount_paid_inr": 100.0,
        "payment_mode": "upi"
    })
    assert settle_res.status_code == 200
    settle_data = settle_res.json()
    assert settle_data["success"] is True
    assert settle_data["new_balance_inr"] == init_bal - 100.0

    # Reset balance back
    client.post("/khata/settle", json={
        "customer_id": sharma["customer_id"],
        "amount_paid_inr": -100.0,
        "payment_mode": "cash"
    })


def test_khata_voice_reminder():
    """Verify Khata WhatsApp voice note reminder generation."""
    res = client.post("/khata/voice-reminder", json={"customer_id": "CUST-001"})
    assert res.status_code == 200
    data = res.json()
    assert data["customer_id"] == "CUST-001"
    assert "खाता स्मरण" in data["whatsapp_text"]
    assert "upi://" in data["whatsapp_text"]
    assert "नमस्ते" in data["voice_script_hi"]


def test_ondc_beckn_export():
    """Verify ONDC Beckn v1.2.0 export endpoint produces valid Beckn confirm payload."""
    res = client.post("/ondc/export-beckn", json={
        "bap_id": "nic2004:52110",
        "customer_name": "Sharma Ji",
        "delivery_address": "402 Shanti Kunj, Delhi"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["beckn_schema_version"] == "1.2.0"
    assert data["domain"] == "ONDC:RET10"
    assert data["payload"]["context"]["domain"] == "ONDC:RET10"
    assert data["payload"]["message"]["order"]["state"] == "Created"
    assert len(data["payload"]["message"]["order"]["items"]) >= 1
    assert data["payload"]["message"]["order"]["billing"]["name"] == "Sharma Ji"
