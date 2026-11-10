"""
Catalogue Matcher Service.
Matches extracted product mentions against the Kirana grocery catalogue using RapidFuzz.
Detects ambiguous product mentions and low-confidence matches to trigger clarification dialogues.
"""
import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from rapidfuzz import fuzz, distance

from backend.app.config import get_catalogue_path, CONFIDENCE_THRESHOLD, AMBIGUITY_DELTA_THRESHOLD
from backend.app.schemas import (
    CatalogueSKU,
    ParsedItem,
    MatchCandidate,
    ProductMatchResult,
    ClarificationQuestion,
    ClarificationOption,
    MatchProductsResponse
)
from backend.app.services.order_parser import make_boundary_regex

logger = logging.getLogger(__name__)

# Predefined ambiguity resolvers for ambiguous Indian grocery item families
AMBIGUITY_FAMILIES: Dict[str, Dict[str, Any]] = {
    "rice": {
        "triggers": ["chawal", "चावल", "rice", "akki", "arisi"],
        "specifics": ["basmati", "बासमती", "india gate", "sona masoori", "सोना मसूरी", "sadharan", "साधारण", "kolam"],
        "question_hi": "'इंडिया गेट बासमती चावल' (₹95/kg) चाहिए या 'सोना मसूरी साधारण चावल' (₹58/kg)?",
        "question_en": "Would you like India Gate Basmati Rice (₹95/kg) or Sona Masoori Regular Rice (₹58/kg)?",
        "sku_ids": ["SKU-002", "SKU-003"]
    },
    "maggi": {
        "triggers": ["maggi", "मैगी", "meghee", "meggi", "noodles"],
        "specifics": ["masala", "मसाला", "atta", "आटा", "veg", "2 minute", "२-मिनट"],
        "question_hi": "'मैगी 2-मिनट मसाला नूडल्स' (₹14) चाहिए या 'मैगी आटा नूडल्स' (₹25)?",
        "question_en": "Would you like Maggi 2-Minute Masala (₹14) or Maggi Veg Atta Noodles (₹25)?",
        "sku_ids": ["SKU-027", "SKU-028"]
    },
    "dal": {
        "triggers": ["dal", "daal", "दाल", "bele", "paruppu"],
        "specifics": ["toor", "तूर", "arhar", "अरहर", "moong", "मूंग", "chana", "चना", "urad", "उड़द", "masoor", "मसूर"],
        "question_hi": "'तूर दाल' (₹140/kg), 'मूंग दाल' (₹128/kg) या 'चना दाल' (₹92/kg) चाहिए?",
        "question_en": "Which dal: Toor Dal (₹140/kg), Moong Dal (₹128/kg), or Chana Dal (₹92/kg)?",
        "sku_ids": ["SKU-007", "SKU-008", "SKU-009"]
    },
    "oil": {
        "triggers": ["tel", "oil", "तेल", "enne", "ennai"],
        "specifics": ["fortune", "फॉर्च्यून", "sunflower", "refined", "sarson", "सरसों", "mustard", "arogyam", "आरोग्यम", "almond", "बादाम", "badam"],
        "question_hi": "'फॉर्च्यून रिफाइंड तेल' (₹145/L), 'आरोग्यम सरसों तेल' (₹158/L) या 'बादाम तेल' (₹65)?",
        "question_en": "Fortune Refined Oil (₹145/L), Mustard Oil (₹158/L), or Hair Oil (₹65)?",
        "sku_ids": ["SKU-016", "SKU-017", "SKU-033"]
    },
    "atta": {
        "triggers": ["atta", "आटा", "aata", "godhi hittu"],
        "specifics": ["aashirvaad", "आशीर्वाद", "chakki", "fortune", "sharbati", "multigrain", "मल्टीग्रेन"],
        "question_hi": "'आशीर्वाद चक्की आटा' (₹52/kg) चाहिए या कोई अन्य प्रकार?",
        "question_en": "Would you prefer Aashirvaad Chakki Atta (₹52/kg)?",
        "sku_ids": ["SKU-001"]
    }
}


class CatalogueMatcher:
    def __init__(self, catalogue_path: Optional[Path] = None):
        path = catalogue_path or get_catalogue_path()
        self.skus: List[CatalogueSKU] = []
        self.sku_lookup: Dict[str, CatalogueSKU] = {}
        self.store_name: str = "Gupta Kirana & General Store"
        self._load_catalogue(path)

    def _load_catalogue(self, path: Path) -> None:
        if not path.exists():
            logger.warning(f"Catalogue file not found at {path}. Initializing empty.")
            return

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.store_name = data.get("store_name", self.store_name)
        raw_skus = data.get("skus", [])
        self.skus = [CatalogueSKU(**s) for s in raw_skus]
        self.sku_lookup = {s.sku_id: s for s in self.skus}
        logger.info(f"Loaded {len(self.skus)} SKUs into CatalogueMatcher from {path}")

    def get_all_skus(self) -> List[CatalogueSKU]:
        return self.skus

    def get_sku(self, sku_id: str) -> Optional[CatalogueSKU]:
        return self.sku_lookup.get(sku_id)

    def check_ambiguity_family(self, phrase: str, item: ParsedItem) -> Optional[ClarificationQuestion]:
        """
        Detects if a generic term triggers a clarification prompt across known ambiguity families.
        Uses boundary-safe regex to prevent false substring matches (e.g. 'akki' inside 'chakki').
        """
        phrase_clean = phrase.strip()

        for fam_key, fam_data in AMBIGUITY_FAMILIES.items():
            # Check if any trigger word is present as a whole word
            trigger_matched = any(
                bool(re.search(make_boundary_regex(t), phrase_clean, re.IGNORECASE))
                for t in fam_data["triggers"]
            )
            if not trigger_matched:
                continue

            # Check if a differentiating specific word is already mentioned as a whole word
            specific_matched = any(
                bool(re.search(make_boundary_regex(s), phrase_clean, re.IGNORECASE))
                for s in fam_data["specifics"]
            )
            if specific_matched:
                # User already specified which one (e.g., "basmati rice"), so no family ambiguity!
                continue

            # Build clarification options
            options = []
            for s_id in fam_data["sku_ids"]:
                sku = self.sku_lookup.get(s_id)
                if sku:
                    options.append(
                        ClarificationOption(
                            sku_id=sku.sku_id,
                            name_en=sku.name_en,
                            name_hi=sku.name_hi,
                            category=sku.category,
                            quantity=item.quantity,
                            unit=sku.unit,
                            price_inr=sku.price_inr
                        )
                    )

            if len(options) > 1:
                return ClarificationQuestion(
                    family=fam_key,
                    spoken_phrase=phrase,
                    question_hi=fam_data["question_hi"],
                    question_en=fam_data["question_en"],
                    options=options,
                    confidence=0.68
                )

        return None

    def match_single_item(self, item: ParsedItem, keyterms_enabled: bool = True) -> ProductMatchResult:
        """
        Matches a single ParsedItem to the catalogue.
        """
        product_query = item.product.strip()
        if not product_query or len(product_query) < 2:
            return ProductMatchResult(
                original_item=item,
                status="UNRECOGNIZED",
                confidence=0.0
            )

        # 1. First check if this query triggers a family ambiguity
        fam_clarification = self.check_ambiguity_family(product_query, item)
        if fam_clarification:
            return ProductMatchResult(
                original_item=item,
                status="CLARIFICATION_REQUIRED",
                confidence=fam_clarification.confidence,
                clarification=fam_clarification
            )

        # 2. Score candidates across catalogue aliases
        scored_candidates: List[MatchCandidate] = []
        query_lower = product_query.lower()

        for sku in self.skus:
            best_sku_score = 0.0
            best_matched_alias = ""

            for alias in sku.aliases:
                alias_lower = alias.lower()

                # 1. Exact alias match
                if alias_lower == query_lower:
                    best_sku_score = 0.99
                    best_matched_alias = alias
                    break

                # 2. Distinct word boundary match in query
                if re.search(make_boundary_regex(alias_lower), query_lower, re.IGNORECASE):
                    # Weight by coverage to avoid tiny matches in completely different queries
                    coverage = len(alias_lower) / max(len(query_lower), 1)
                    score = min(0.96, 0.85 + (0.11 * coverage)) if keyterms_enabled else min(0.88, 0.75 + (0.13 * coverage))
                    if score > best_sku_score:
                        best_sku_score = score
                        best_matched_alias = alias
                    continue

                # 3. Fuzzy similarity using full token set ratio and ratio
                if len(alias_lower) >= 3 and len(query_lower) >= 3:
                    token_ratio = fuzz.token_sort_ratio(alias_lower, query_lower) / 100.0
                    full_ratio = fuzz.ratio(alias_lower, query_lower) / 100.0
                    score = max(token_ratio, full_ratio)

                    # Only consider if there is meaningful overlap
                    if score >= 0.55 and score > best_sku_score:
                        best_sku_score = score
                        best_matched_alias = alias

            if best_sku_score >= 0.55:
                scored_candidates.append(
                    MatchCandidate(
                        sku_id=sku.sku_id,
                        name_en=sku.name_en,
                        name_hi=sku.name_hi,
                        unit=sku.unit,
                        price_inr=sku.price_inr,
                        score=round(best_sku_score, 3),
                        matched_alias=best_matched_alias
                    )
                )

        scored_candidates.sort(key=lambda c: c.score, reverse=True)

        if not scored_candidates:
            return ProductMatchResult(
                original_item=item,
                status="UNRECOGNIZED",
                confidence=0.0
            )

        top_candidate = scored_candidates[0]
        top_sku = self.sku_lookup[top_candidate.sku_id]

        # 3. Check for close score ambiguity between top 2 candidates
        if len(scored_candidates) >= 2:
            second = scored_candidates[1]
            if (top_candidate.score - second.score) < AMBIGUITY_DELTA_THRESHOLD and top_candidate.score < 0.92:
                second_sku = self.sku_lookup[second.sku_id]
                clarification = ClarificationQuestion(
                    family="ambiguous_match",
                    spoken_phrase=item.product,
                    question_hi=f"क्या आपको '{top_sku.name_hi}' (₹{top_sku.price_inr}) चाहिए या '{second_sku.name_hi}' (₹{second_sku.price_inr})?",
                    question_en=f"Did you mean '{top_sku.name_en}' (₹{top_sku.price_inr}) or '{second_sku.name_en}' (₹{second_sku.price_inr})?",
                    options=[
                        ClarificationOption(
                            sku_id=top_sku.sku_id,
                            name_en=top_sku.name_en,
                            name_hi=top_sku.name_hi,
                            category=top_sku.category,
                            quantity=item.quantity,
                            unit=top_sku.unit,
                            price_inr=top_sku.price_inr
                        ),
                        ClarificationOption(
                            sku_id=second_sku.sku_id,
                            name_en=second_sku.name_en,
                            name_hi=second_sku.name_hi,
                            category=second_sku.category,
                            quantity=item.quantity,
                            unit=second_sku.unit,
                            price_inr=second_sku.price_inr
                        )
                    ],
                    confidence=top_candidate.score
                )
                return ProductMatchResult(
                    original_item=item,
                    status="CLARIFICATION_REQUIRED",
                    confidence=top_candidate.score,
                    clarification=clarification,
                    candidates=scored_candidates[:4]
                )

        # 4. Check confidence threshold
        if top_candidate.score >= CONFIDENCE_THRESHOLD:
            return ProductMatchResult(
                original_item=item,
                status="MATCHED",
                confidence=top_candidate.score,
                matched_sku=top_sku,
                candidates=scored_candidates[:3]
            )
        elif top_candidate.score >= 0.55:
            # Borderline score requires confirmation
            clarification = ClarificationQuestion(
                family="low_confidence",
                spoken_phrase=item.product,
                question_hi=f"क्या आपने '{top_sku.name_hi}' कहा?",
                question_en=f"Did you say '{top_sku.name_en}'?",
                options=[
                    ClarificationOption(
                        sku_id=top_sku.sku_id,
                        name_en=top_sku.name_en,
                        name_hi=top_sku.name_hi,
                        category=top_sku.category,
                        quantity=item.quantity,
                        unit=top_sku.unit,
                        price_inr=top_sku.price_inr
                    )
                ],
                confidence=top_candidate.score
            )
            return ProductMatchResult(
                original_item=item,
                status="CLARIFICATION_REQUIRED",
                confidence=top_candidate.score,
                clarification=clarification,
                candidates=scored_candidates[:3]
            )
        else:
            return ProductMatchResult(
                original_item=item,
                status="UNRECOGNIZED",
                confidence=top_candidate.score,
                candidates=scored_candidates[:2]
            )

    def match_items(self, items: List[ParsedItem], keyterms_enabled: bool = True) -> MatchProductsResponse:
        matched: List[ProductMatchResult] = []
        clarifications: List[ClarificationQuestion] = []
        unmatched: List[ParsedItem] = []

        for item in items:
            result = self.match_single_item(item, keyterms_enabled=keyterms_enabled)
            matched.append(result)

            if result.status == "CLARIFICATION_REQUIRED" and result.clarification:
                clarifications.append(result.clarification)
            elif result.status == "UNRECOGNIZED":
                unmatched.append(item)

        return MatchProductsResponse(
            matched_items=matched,
            clarifications_needed=clarifications,
            unmatched_items=unmatched
        )


# Default singleton instance
catalogue_matcher = CatalogueMatcher()
