"""
Unit tests for CatalogueMatcher.
Tests catalogue loading, RapidFuzz alias matching, ambiguity detection, and clarification questions.
"""
import pytest
from backend.app.schemas import ParsedItem
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
