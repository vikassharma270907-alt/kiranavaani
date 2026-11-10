"""
Unit tests for CatalogueMatcher.
Tests catalogue loading, RapidFuzz alias matching, ambiguity detection, clarification questions,
out-of-stock substitutions, budget allocations, and price lookups.
"""
import pytest
from backend.app.schemas import ParsedItem, CartItemInput
from backend.app.services.catalogue_matcher import catalogue_matcher


def test_catalogue_minimum_skus():
    """Verify sample catalogue contains at least 30 grocery products."""
    skus = catalogue_matcher.get_all_skus()
    assert len(skus) >= 30, f"Expected >= 30 SKUs, got {len(skus)}"


def test_direct_product_match():
    """Verify known unambiguous items match directly with high confidence."""
    item = ParsedItem(product="Sugar", quantity=1.0, unit="kg")
    res = catalogue_matcher.match_single_item(item)
    assert res.status == "MATCHED"
    assert res.matched_sku is not None
    assert "Sugar" in res.matched_sku.name_en
    assert res.confidence >= 0.78


def test_ambiguity_family_chawal():
    """
    Verify generic 'chawal' / 'rice' triggers CLARIFICATION_REQUIRED
    with options for Basmati vs Sona Masoori.
    """
    item = ParsedItem(product="chawal", quantity=1.0, unit="kg")
    res = catalogue_matcher.match_single_item(item)
    assert res.status == "CLARIFICATION_REQUIRED"
    assert res.clarification is not None
    assert res.clarification.family == "rice"
    assert len(res.clarification.options) >= 2


def test_specific_rice_bypasses_ambiguity():
    """Verify specific 'basmati chawal' directly matches without asking for clarification."""
    item = ParsedItem(product="India Gate Basmati chawal", quantity=1.0, unit="kg")
    res = catalogue_matcher.match_single_item(item)
    assert res.status == "MATCHED"
    assert res.matched_sku is not None
    assert res.matched_sku.sku_id == "SKU-002"


def test_unrecognized_product():
    """Verify completely unknown strings are categorized as UNRECOGNIZED."""
    item = ParsedItem(product="unknown_spacecraft_component_xyz", quantity=1.0, unit="piece")
    res = catalogue_matcher.match_single_item(item)
    assert res.status == "UNRECOGNIZED"
    assert res.matched_sku is None


def test_ambiguity_family_maggi_dal_oil():
    """Verify other generic grocery families (Maggi, Dal, Oil) trigger clarification dialogues."""
    # 1. Generic Maggi
    maggi_item = ParsedItem(product="Maggi", quantity=2.0, unit="packet")
    res_m = catalogue_matcher.match_single_item(maggi_item)
    assert res_m.status == "CLARIFICATION_REQUIRED"
    assert res_m.clarification.family == "maggi"

    # 2. Generic Dal
    dal_item = ParsedItem(product="daal", quantity=1.0, unit="kg")
    res_d = catalogue_matcher.match_single_item(dal_item)
    assert res_d.status == "CLARIFICATION_REQUIRED"
    assert res_d.clarification.family == "dal"

    # 3. Generic Oil
    oil_item = ParsedItem(product="tel", quantity=1.0, unit="litre")
    res_o = catalogue_matcher.match_single_item(oil_item)
    assert res_o.status == "CLARIFICATION_REQUIRED"
    assert res_o.clarification.family == "oil"


def test_resolve_spoken_clarification():
    """Verify resolving spoken clarification answers directly into matched SKUs."""
    # Resolve 'basmati' in rice family
    resolved_basmati = catalogue_matcher.resolve_spoken_clarification("rice", "India Gate Basmati rice")
    assert resolved_basmati is not None
    sku, score = resolved_basmati
    assert sku.sku_id == "SKU-002"
    assert score >= 0.65

    # Resolve 'sona masoori' in rice family
    resolved_sona = catalogue_matcher.resolve_spoken_clarification("rice", "sadharan sona masoori chawal")
    assert resolved_sona is not None
    assert resolved_sona[0].sku_id == "SKU-003"

    # Non-existent family returns None
    assert catalogue_matcher.resolve_spoken_clarification("unknown_family_xyz", "some text") is None


def test_stock_management_and_substitutions():
    """Verify stock toggle and substitute SKU lookup methods."""
    # Toggle stock of SKU-013 (Amul Butter)
    assert catalogue_matcher.set_sku_stock("SKU-013", False) is True
    assert catalogue_matcher.get_sku("SKU-013").in_stock is False

    # Get substitute for out of stock butter
    sub = catalogue_matcher.get_substitute_for_sku("SKU-013")
    assert sub is not None
    assert sub.in_stock is True

    # Re-enable stock
    catalogue_matcher.set_sku_stock("SKU-013", True)
    assert catalogue_matcher.get_sku("SKU-013").in_stock is True

    # Non-existent SKU handling
    assert catalogue_matcher.set_sku_stock("SKU-NONEXISTENT", False) is False
    assert catalogue_matcher.get_substitute_for_sku("SKU-NONEXISTENT") is None


def test_advise_budget_calculations():
    """Verify budget advisory calculation under tight, zero, and standard caps."""
    # Standard allocation
    adv = catalogue_matcher.advise_budget(
        budget_inr=500.0,
        mandatory_items=[CartItemInput(sku_id="SKU-001", quantity=2.0)],  # ₹104
        filler_product_query="sugar"
    )
    assert adv.allocated_total_inr <= 500.0
    assert adv.remaining_balance_inr >= 0.0
    assert adv.suggested_filler_quantity > 0.0

    # Zero budget cap
    adv_zero = catalogue_matcher.advise_budget(
        budget_inr=0.0,
        mandatory_items=[]
    )
    assert adv_zero.allocated_total_inr == 0.0
    assert adv_zero.remaining_balance_inr == 0.0


def test_lookup_price_quotes_multi_match():
    """Verify price quote search formats answers for single vs multiple matches."""
    # Single specific quote
    q_single = catalogue_matcher.lookup_price_quotes("Aashirvaad Atta")
    assert q_single.found is True
    assert len(q_single.items) >= 1
    assert "आटा" in q_single.spoken_answer_hi

    # Unrecognized item
    q_none = catalogue_matcher.lookup_price_quotes("completely_unknown_gadget_xyz")
    assert q_none.found is False
    assert len(q_none.items) == 0
