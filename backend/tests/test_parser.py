"""
Unit tests for HinglishOrderParser.
Tests fractional numeral conversion, unit normalization, clause extraction, and completion signals.
"""
import pytest
from backend.app.services.order_parser import order_parser


def test_numeral_normalization_fractions():
    cases = [
        ("aadha litre milk", "0.5 litre milk"),
        ("dedh kilo sugar", "1.5 kilo sugar"),
        ("dhai kilo chawal", "2.5 kilo chawal"),
        ("sawa do packet biscuit", "2.25 packet biscuit"),
        ("paune do kilo atta", "1.75 kilo atta"),
        ("saadhe teen litre tel", "3.5 litre tel"),
    ]
    for raw, expected in cases:
        normalized = order_parser.normalize_numerals(raw)
        assert expected in normalized, f"Failed for '{raw}': got '{normalized}'"


def test_numeral_normalization_devanagari():
    cases = [
        ("आधा लीटर दूध", "0.5 लीटर दूध"),
        ("डेढ़ किलो चीनी", "1.5 किलो चीनी"),
        ("ढाई किलो चावल", "2.5 किलो चावल"),
        ("सवा दो पैकेट बिस्किट", "2.25 पैकेट बिस्किट"),
        ("पौने दो किलो आटा", "1.75 किलो आटा"),
        ("साढ़े तीन लीटर तेल", "3.5 लीटर तेल"),
    ]
    for raw, expected in cases:
        normalized = order_parser.normalize_numerals(raw)
        assert expected in normalized, f"Failed for '{raw}': got '{normalized}'"


def test_cardinal_numerals():
    cases = [
        ("ek kilo", "1 kilo"),
        ("do packet", "2 packet"),
        ("teen bottle", "3 bottle"),
        ("chaar pack", "4 pack"),
        ("paanch kilo", "5 kilo"),
        ("दस पैकेट", "10 पैकेट"),
    ]
    for raw, expected in cases:
        normalized = order_parser.normalize_numerals(raw)
        assert expected in normalized, f"Failed for '{raw}': got '{normalized}'"


def test_unit_normalization():
    test_clauses = [
        ("2 packet Maggi", 2.0, "packet", "Maggi"),
        ("1 kilo sugar", 1.0, "kg", "sugar"),
        ("0.5 litre milk", 0.5, "litre", "milk"),
        ("500 gm toor dal", 500.0, "gram", "toor dal"),
        ("1 bottle oil", 1.0, "bottle", "oil"),
    ]
    for clause, exp_qty, exp_unit, exp_prod in test_clauses:
        qty, unit, prod = order_parser.extract_quantity_and_unit(clause)
        assert qty == exp_qty
        assert unit == exp_unit
        assert exp_prod.lower() in prod.lower()


def test_full_utterance_parsing():
    transcript = "Bhaiya, do packet Maggi, ek kilo sugar aur aadha litre milk bhej dena."
    res = order_parser.parse_utterance(transcript)

    assert len(res.items) == 3
    items_by_prod = {i.product.lower(): i for i in res.items}

    # Verify Maggi
    assert any("maggi" in k for k in items_by_prod)
    maggi_item = next(v for k, v in items_by_prod.items() if "maggi" in k)
    assert maggi_item.quantity == 2.0
    assert maggi_item.unit == "packet"

    # Verify Sugar
    assert any("sugar" in k for k in items_by_prod)
    sugar_item = next(v for k, v in items_by_prod.items() if "sugar" in k)
    assert sugar_item.quantity == 1.0
    assert sugar_item.unit == "kg"

    # Verify Milk
    assert any("milk" in k for k in items_by_prod)
    milk_item = next(v for k, v in items_by_prod.items() if "milk" in k)
    assert milk_item.quantity == 0.5
    assert milk_item.unit == "litre"


def test_order_completion_detection():
    assert order_parser.check_order_completion("bas itna hi bhaiya") is True
    assert order_parser.check_order_completion("ho gaya bill bana do") is True
    assert order_parser.check_order_completion("ek kilo chawal dena") is False


def test_completion_verb_does_not_corrupt_product_name():
    """Verify verbs like 'pack kar do' are stripped without converting 'do' into numeral 2."""
    raw = "Gupta ji do kilo chawal aur ek packet Tata Salt pack kar do."
    res = order_parser.parse_utterance(raw)
    assert res.is_order_complete is True
    prods = [i.product.strip() for i in res.items]
    assert "Tata Salt" in prods
    assert "Tata Salt pack kar 2" not in prods


def test_kannada_and_tamil_numerals():
    """Verify Kannada and Tamil numeral fractions normalize properly."""
    cases = [
        ("ondu kilo atta", "1 kilo atta"),
        ("eradu packet maggi", "2 packet maggi"),
        ("ardha litre milk", "0.5 litre milk"),
        ("kaalu kilo toor dal", "0.25 kilo toor dal"),
        ("ondavare kilo sugar", "1.5 kilo sugar"),
        ("oru kilo rice", "1 kilo rice"),
        ("rendu packet biscuit", "2 packet biscuit"),
        ("ara litre tel", "0.5 litre tel"),
    ]
    for raw, expected in cases:
        normalized = order_parser.normalize_numerals(raw)
        assert expected in normalized, f"Failed for '{raw}': got '{normalized}'"


def test_pao_and_darjan_units():
    """Verify traditional Indian market fractions: pao, aadha pao, and darjan."""
    cases = [
        ("paav bhar paneer", "0.25 paneer"),
        ("aadha paav mirch", "0.125 mirch"),
        ("darjan ande", "12 ande"),
        ("aadha darjan biscuit", "6 biscuit"),
    ]
    for raw, expected in cases:
        normalized = order_parser.normalize_numerals(raw)
        assert expected in normalized, f"Failed for '{raw}': got '{normalized}'"


def test_khata_extraction():
    """Verify Kirana credit ledger (khata / udhaar) detection and customer name extraction."""
    res1 = order_parser.parse_utterance("Sharma ji ke khaate me likh lo bhaiya, 2 packet maggi")
    assert res1.khata_info is not None
    assert res1.khata_info.is_khata is True
    assert "Sharma" in res1.khata_info.customer_name
    assert res1.khata_info.payment_mode == "khata"

    res2 = order_parser.parse_utterance("Gupta ji 1 kilo sugar pack kar do, paise kal sham ko dunga")
    assert res2.khata_info is not None
    assert res2.khata_info.is_khata is True

    res3 = order_parser.parse_utterance("2 packet kurkure dena, bas itna hi")
    assert res3.khata_info is None or res3.khata_info.is_khata is False


def test_kannada_tamil_completion():
    """Verify Dravidian completion triggers like 'saaku', 'aste', 'avlo dhaan'."""
    assert order_parser.check_order_completion("ondu packet maggi kodi, aste") is True
    assert order_parser.check_order_completion("eradu kilo rice, saaku") is True
    assert order_parser.check_order_completion("oru litre oil, avlo dhaan") is True


def test_bhasha_sudhaar_quantity_correction():
    """Verify Bhasha-Sudhaar mid-sentence quantity repair ('5 nahi 2 kilo karna')."""
    transcript = "Bhaiya 5 kilo आशीर्वाद आटा, नहीं नहीं 5 नहीं 2 kilo कर दो, और 1 packet Maggi."
    res = order_parser.parse_utterance(transcript)
    
    assert len(res.repairs_applied) > 0
    correction = next((r for r in res.repairs_applied if r.action == "CORRECTED_QUANTITY"), None)
    assert correction is not None
    assert correction.previous_quantity == 5.0
    assert correction.new_quantity == 2.0

    # Ensure atta is in items with quantity 2.0
    atta_item = next((it for it in res.items if "आटा" in it.product or "atta" in it.product.lower()), None)
    assert atta_item is not None
    assert atta_item.quantity == 2.0


def test_bhasha_sudhaar_item_cancellation():
    """Verify Bhasha-Sudhaar verbal item cancellation ('butter mat bhejna cancel kar do')."""
    transcript = "2 packet Maggi aur 1 Amul butter, arre nahi butter mat bhejna cancel kar do."
    res = order_parser.parse_utterance(transcript)

    assert len(res.repairs_applied) > 0
    cancellation = next((r for r in res.repairs_applied if r.action == "CANCELLED_ITEM"), None)
    assert cancellation is not None
    assert "butter" in cancellation.product.lower()

    # Butter should NOT be in active items
    assert not any("butter" in it.product.lower() for it in res.items)
    # Maggi should remain
    assert any("maggi" in it.product.lower() for it in res.items)


def test_bhav_pucho_intent_detection():
    """Verify Bhav Pucho rate check vs ordering intent classification."""
    inquiry_res = order_parser.parse_utterance("Basmati chawal ka kya bhav chal raha hai?")
    assert inquiry_res.detected_intent == "PRICE_INQUIRY"
    assert inquiry_res.price_inquiry_item is not None

    budget_res = order_parser.parse_utterance("500 rupaye ke andar rashan bana do")
    assert budget_res.detected_intent == "BUDGET_QUERY"
    assert budget_res.budget_cap_inr == 500.0

    normal_res = order_parser.parse_utterance("2 packet Maggi aur 1 kilo sugar dena")
    assert normal_res.detected_intent == "ORDER"
