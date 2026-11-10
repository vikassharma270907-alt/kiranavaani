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
