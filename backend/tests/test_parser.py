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
