"""
Catalogue Matcher Service.
Matches extracted product mentions against the Kirana grocery catalogue using RapidFuzz.
Detects ambiguous product mentions and low-confidence matches to trigger clarification dialogues.
"""
from __future__ import annotations
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
    MatchProductsResponse,
    SubstitutionSuggestion,
    PriceQuoteItem,
    PriceInquiryResponse,
    BudgetAdvisorResponse,
    BhaavTaalResponse,
    BargainItemDetail,
    RecipeIngredientItem,
    RecipeToCartResponse
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


# Default substitute recommendations if an SKU goes out of stock in a Kirana store
DEFAULT_SUBSTITUTIONS: Dict[str, List[str]] = {
    "SKU-013": ["SKU-014", "SKU-015"],  # Amul Butter -> Amul Paneer or Mother Dairy Curd
    "SKU-002": ["SKU-003"],             # India Gate Basmati -> Sona Masoori Rice
    "SKU-003": ["SKU-002"],             # Sona Masoori -> Basmati Rice
    "SKU-016": ["SKU-017"],             # Fortune Sunflower Oil -> Arogyam Mustard Oil
    "SKU-017": ["SKU-016"],             # Mustard Oil -> Sunflower Oil
    "SKU-027": ["SKU-028"],             # Maggi 2-Min -> Maggi Veg Atta Noodles
    "SKU-028": ["SKU-027"],             # Maggi Atta -> Maggi 2-Min
    "SKU-031": ["SKU-032"],             # Parle-G -> Britannia Good Day
    "SKU-024": ["SKU-025"],             # Red Label Tea -> Tata Tea Gold
    "SKU-007": ["SKU-008", "SKU-009"]   # Toor Dal -> Moong Dal or Chana Dal
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
        self.skus = []
        for s in raw_skus:
            sku_obj = CatalogueSKU(**s)
            # Attach default substitutes if not in json
            if not sku_obj.substitutes and sku_obj.sku_id in DEFAULT_SUBSTITUTIONS:
                sku_obj.substitutes = DEFAULT_SUBSTITUTIONS[sku_obj.sku_id]
            self.skus.append(sku_obj)
        self.sku_lookup = {s.sku_id: s for s in self.skus}
        logger.info(f"Loaded {len(self.skus)} SKUs into CatalogueMatcher from {path}")

    def set_sku_stock(self, sku_id: str, in_stock: bool) -> bool:
        """Toggles in-stock status for a given SKU (merchant inventory control)."""
        sku = self.sku_lookup.get(sku_id)
        if sku:
            sku.in_stock = in_stock
            logger.info(f"Updated {sku_id} ({sku.name_en}) stock status to {in_stock}")
            return True
        return False

    def get_substitute_for_sku(self, sku_id: str) -> Optional[CatalogueSKU]:
        """Finds the best available in-stock substitute for an out-of-stock item."""
        sku = self.sku_lookup.get(sku_id)
        if not sku:
            return None

        # 1. Check direct configured substitutes
        for sub_id in (sku.substitutes or []):
            candidate = self.sku_lookup.get(sub_id)
            if candidate and candidate.in_stock:
                return candidate

        # 2. Fallback to same category in-stock items
        for candidate in self.skus:
            if candidate.sku_id != sku.sku_id and candidate.category == sku.category and candidate.in_stock:
                return candidate

        return None

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
        product_query = re.sub(r"[^\w\s\u0900-\u0963\u0966-\u097F\u0C80-\u0CFF\u0B80-\u0BFF\-]", "", item.product).strip()
        if not product_query or len(product_query) < 2 or product_query.lower() in ("ही", "hi", "to", "तो", "ka", "ki", "ke", "ko", "se", "me", "pe"):
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
            # Check stock availability
            if not getattr(top_sku, "in_stock", True):
                sub_sku = self.get_substitute_for_sku(top_sku.sku_id)
                if sub_sku:
                    substitution = SubstitutionSuggestion(
                        original_item_name=top_sku.name_en,
                        out_of_stock_sku=top_sku,
                        substitute_sku=sub_sku,
                        reason_hi=f"'{top_sku.name_hi}' अभी उपलब्ध नहीं है। क्या '{sub_sku.name_hi}' (₹{sub_sku.price_inr}) चलेगा?",
                        reason_en=f"'{top_sku.name_en}' is out of stock. Would you prefer '{sub_sku.name_en}' (₹{sub_sku.price_inr})?",
                        spoken_prompt_hi=f"'{top_sku.name_hi}' अभी दुकान में खत्म है। इसके बदले '{sub_sku.name_hi}' दे दें?",
                        spoken_prompt_en=f"'{top_sku.name_en}' is out of stock. Shall I substitute with '{sub_sku.name_en}'?"
                    )
                    return ProductMatchResult(
                        original_item=item,
                        status="OUT_OF_STOCK_SUBSTITUTION",
                        confidence=top_candidate.score,
                        matched_sku=top_sku,
                        substitution=substitution,
                        candidates=scored_candidates[:3]
                    )

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
        substitutions: List[SubstitutionSuggestion] = []
        unmatched: List[ParsedItem] = []

        for item in items:
            result = self.match_single_item(item, keyterms_enabled=keyterms_enabled)
            matched.append(result)

            if result.status == "CLARIFICATION_REQUIRED" and result.clarification:
                clarifications.append(result.clarification)
            elif result.status == "OUT_OF_STOCK_SUBSTITUTION" and result.substitution:
                substitutions.append(result.substitution)
            elif result.status == "UNRECOGNIZED":
                unmatched.append(item)

        return MatchProductsResponse(
            matched_items=matched,
            clarifications_needed=clarifications,
            substitutions_needed=substitutions,
            unmatched_items=unmatched
        )

    def resolve_spoken_clarification(self, family: str, utterance: str) -> Optional[Tuple[CatalogueSKU, float]]:
        """
        Resolves a spoken clarification answer (e.g. 'basmati wala', 'sona masoori', 'atta maggi')
        to one of the SKUs in that family without requiring mouse clicks.
        """
        fam = AMBIGUITY_FAMILIES.get(family.lower())
        if not fam:
            return None

        clean_utt = utterance.lower().strip()
        best_sku: Optional[CatalogueSKU] = None
        best_score = 0.0

        for sku_id in fam["sku_ids"]:
            sku = self.sku_lookup.get(sku_id)
            if not sku:
                continue

            candidates = [sku.name_en.lower(), sku.name_hi.lower()] + [a.lower() for a in sku.aliases]
            for cand in candidates:
                ratio = fuzz.partial_ratio(cand, clean_utt) / 100.0
                token_ratio = fuzz.token_set_ratio(cand, clean_utt) / 100.0
                score = max(ratio, token_ratio)
                if score > best_score:
                    best_score = score
                    best_sku = sku

        if best_sku and best_score >= 0.65:
            return best_sku, best_score
        return None

    def lookup_price_quotes(self, query: str) -> PriceInquiryResponse:
        """
        'Bhav Pucho' price lookup: Searches catalogue for matched SKUs and formats spoken quote.
        """
        clean_q = query.lower().strip()
        scored: List[Tuple[CatalogueSKU, float]] = []
        for sku in self.get_all_skus():
            aliases = [sku.name_en.lower(), sku.name_hi.lower()] + [a.lower() for a in sku.aliases]
            best_s = 0.0
            for a in aliases:
                s = fuzz.partial_ratio(a, clean_q) / 100.0
                if s > best_s:
                    best_s = s
            if best_s >= 0.60:
                scored.append((sku, best_s))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        top_skus = [s[0] for s in scored[:3]]

        if not top_skus:
            return PriceInquiryResponse(
                query=query,
                found=False,
                items=[],
                spoken_answer_hi=f"माफ़ कीजिए, '{query}' का भाव हमारे कैटलॉग में नहीं मिला।",
                spoken_answer_en=f"Sorry, price for '{query}' was not found in our catalogue."
            )

        quote_items = [
            PriceQuoteItem(
                sku_id=sku.sku_id,
                name_en=sku.name_en,
                name_hi=sku.name_hi,
                category=sku.category,
                price_inr=sku.price_inr,
                unit=sku.unit,
                in_stock=sku.in_stock
            )
            for sku in top_skus
        ]

        if len(top_skus) == 1:
            it = top_skus[0]
            hi = f"{it.name_hi} का भाव {int(it.price_inr)} रुपये प्रति {it.unit} है।"
            en = f"{it.name_en} is priced at ₹{it.price_inr:g} per {it.unit}."
        else:
            hi_parts = [f"{it.name_hi} {int(it.price_inr)} रुपये प्रति {it.unit}" for it in top_skus[:2]]
            en_parts = [f"{it.name_en} is ₹{it.price_inr:g}/{it.unit}" for it in top_skus[:2]]
            hi = f"{', '.join(hi_parts)} है। क्या कार्ट में जोड़ना है?"
            en = f"{' and '.join(en_parts)}. Would you like to add this to your cart?"

        return PriceInquiryResponse(
            query=query,
            found=True,
            items=quote_items,
            spoken_answer_hi=hi,
            spoken_answer_en=en
        )

    def advise_budget(
        self,
        budget_inr: float,
        mandatory_items: List[Any],
        filler_product_query: Optional[str] = "sugar"
    ) -> BudgetAdvisorResponse:
        """
        'Budget-Aware Kirana Basket':
        Given a budget cap (e.g. ₹500), computes cost of mandatory items and suggests
        optimal filler quantity of requested staple (e.g. sugar or tea).
        """
        mandatory_cost = 0.0
        for m in mandatory_items:
            sku = self.sku_lookup.get(getattr(m, "sku_id", None) or m.get("sku_id"))
            if sku:
                qty = getattr(m, "quantity", 1.0) if hasattr(m, "quantity") else m.get("quantity", 1.0)
                mandatory_cost += sku.price_inr * qty

        remaining = max(0.0, budget_inr - mandatory_cost)
        
        filler_sku = self.sku_lookup.get("SKU-020")  # Madhur Sugar
        if filler_product_query:
            quotes = self.lookup_price_quotes(filler_product_query)
            if quotes.found and quotes.items:
                filler_sku = self.sku_lookup.get(quotes.items[0].sku_id) or filler_sku

        suggested_qty = 0.0
        if filler_sku and filler_sku.price_inr > 0 and remaining > 0:
            raw_qty = remaining / filler_sku.price_inr
            suggested_qty = round(raw_qty * 2) / 2
            if suggested_qty == 0 and raw_qty > 0.2:
                suggested_qty = 0.25

        allocated_total = round(mandatory_cost + (suggested_qty * (filler_sku.price_inr if filler_sku else 0)), 2)
        rem_balance = round(max(0.0, budget_inr - allocated_total), 2)

        hi_msg = (
            f"आपके ₹{budget_inr:g} के बजट में ज़रूरी सामान ₹{mandatory_cost:g} का हुआ। "
            f"बचे हुए ₹{remaining:g} में {suggested_qty:g} {filler_sku.unit if filler_sku else ''} "
            f"{filler_sku.name_hi if filler_sku else ''} जोड़ा जा सकता है।"
        )
        en_msg = (
            f"Within your ₹{budget_inr:g} budget, required items cost ₹{mandatory_cost:g}. "
            f"With the remaining ₹{remaining:g}, you can add {suggested_qty:g} {filler_sku.unit if filler_sku else ''} "
            f"of {filler_sku.name_en if filler_sku else ''}."
        )

        return BudgetAdvisorResponse(
            budget_inr=budget_inr,
            allocated_total_inr=allocated_total,
            remaining_balance_inr=rem_balance,
            mandatory_items_cost=round(mandatory_cost, 2),
            suggested_filler_item=filler_sku,
            suggested_filler_quantity=suggested_qty,
            advice_hi=hi_msg,
            advice_en=en_msg
        )

    def compute_bhaav_taal(
        self,
        cart_items: List[Any],
        customer_id: str = "CUST-001",
        customer_name: str = "Sharma Ji (शर्मा जी)",
        target_discount_pct: Optional[float] = None
    ) -> BhaavTaalResponse:
        """
        'Bhaav-Taal' (भाव-तोल) Dynamic Kirana Margin & Bargaining Engine:
        Analyzes basket items against wholesale APMC Mandi costs, evaluates merchant gross margin headroom,
        checks customer relationship loyalty (Sharma Ji / Verma Ji), and computes a win-win negotiated counter-offer
        alongside warm Indian shopkeeper banter.
        """
        wholesale_rates: Dict[str, float] = {
            "SKU-001": 44.0, "SKU-002": 80.0, "SKU-003": 48.0, "SKU-004": 38.0,
            "SKU-005": 36.0, "SKU-006": 42.0, "SKU-007": 118.0, "SKU-008": 105.0,
            "SKU-009": 76.0, "SKU-010": 110.0, "SKU-011": 122.0, "SKU-012": 28.0,
            "SKU-013": 48.0, "SKU-014": 74.0, "SKU-015": 28.0, "SKU-016": 122.0,
            "SKU-017": 132.0, "SKU-018": 270.0, "SKU-019": 22.0, "SKU-020": 38.0,
            "SKU-021": 25.0, "SKU-022": 38.0, "SKU-023": 28.0, "SKU-024": 115.0,
            "SKU-025": 140.0, "SKU-026": 160.0, "SKU-027": 11.5, "SKU-028": 20.5,
            "SKU-029": 16.0, "SKU-030": 16.0, "SKU-031": 8.0, "SKU-032": 25.0,
            "SKU-033": 52.0, "SKU-034": 75.0, "SKU-035": 16.0
        }

        # If cart is empty, use sample standard high-volume staples for demonstration
        effective_items = list(cart_items)
        if not effective_items:
            effective_items = [
                {"sku_id": "SKU-001", "quantity": 10.0},  # 10kg Aashirvaad Atta
                {"sku_id": "SKU-002", "quantity": 5.0}    # 5kg Basmati Rice
            ]

        bargain_details: List[BargainItemDetail] = []
        tot_retail = 0.0
        tot_wholesale = 0.0

        for it in effective_items:
            sid = getattr(it, "sku_id", None) or it.get("sku_id")
            qty = getattr(it, "quantity", 1.0) if hasattr(it, "quantity") else it.get("quantity", 1.0)
            sku = self.sku_lookup.get(sid)
            if not sku:
                continue

            retail_rate = sku.price_inr
            ws_rate = wholesale_rates.get(sid, round(retail_rate * 0.82, 2))
            line_ret = round(retail_rate * qty, 2)
            line_ws = round(ws_rate * qty, 2)
            tot_retail += line_ret
            tot_wholesale += line_ws

        gross_margin = max(0.0, tot_retail - tot_wholesale)
        margin_pct = (gross_margin / tot_retail * 100) if tot_retail > 0 else 18.0

        # Loyalty multiplier
        loyalty_tier = "GOLD_LOYALTY (पुराने विश्वस्त ग्राहक)"
        discount_rate = 0.06  # 6% default base concession
        if "sharma" in customer_name.lower() or "शर्मा" in customer_name.lower():
            loyalty_tier = "PLATINUM_LOYALTY (शर्मा जी - 5 वर्ष पुराना खाता)"
            discount_rate = 0.075
        elif "verma" in customer_name.lower():
            loyalty_tier = "GOLD_LOYALTY (वर्मा जी - नियमित ग्राहक)"
            discount_rate = 0.065

        # If user explicitly requested e.g. 5% or 10%, accommodate up to 8.5%
        if target_discount_pct is not None:
            discount_rate = min(max(0.03, target_discount_pct / 100.0), 0.09)

        # Ensure merchant preserves at least 8.0% net margin
        max_allowable_discount = max(0.0, gross_margin - (tot_wholesale * 0.08))
        calculated_discount = min(tot_retail * discount_rate, max_allowable_discount)
        
        # Round discount to friendly Indian rupee values (e.g. ₹20, ₹25, ₹35, ₹50)
        friendly_discount = max(10.0, round(calculated_discount / 5.0) * 5.0)
        if friendly_discount >= tot_retail:
            friendly_discount = round(tot_retail * 0.05, 2)

        negotiated_total = round(max(0.0, tot_retail - friendly_discount), 2)
        effective_disc_pct = round((friendly_discount / tot_retail * 100), 1) if tot_retail > 0 else 6.0
        preserved_margin_pct = round(((negotiated_total - tot_wholesale) / negotiated_total * 100), 1) if negotiated_total > 0 else 10.0

        # Populate per-item breakdown
        ratio = (tot_retail - friendly_discount) / tot_retail if tot_retail > 0 else 0.94
        for it in effective_items:
            sid = getattr(it, "sku_id", None) or it.get("sku_id")
            qty = getattr(it, "quantity", 1.0) if hasattr(it, "quantity") else it.get("quantity", 1.0)
            sku = self.sku_lookup.get(sid)
            if not sku:
                continue
            ret = sku.price_inr
            ws = wholesale_rates.get(sid, round(ret * 0.82, 2))
            offered = round(ret * ratio, 2)
            line_orig = round(ret * qty, 2)
            line_disc = round(offered * qty, 2)
            line_margin = round(line_disc - (ws * qty), 2)

            bargain_details.append(BargainItemDetail(
                sku_id=sid,
                name_en=sku.name_en,
                name_hi=sku.name_hi,
                quantity=qty,
                unit=sku.unit,
                retail_rate_inr=ret,
                wholesale_cost_inr=ws,
                offered_rate_inr=offered,
                line_original_inr=line_orig,
                line_discounted_inr=line_disc,
                margin_preserved_inr=line_margin
            ))

        hi_speech = (
            f"अरे {customer_name}! आप तो अपने पुराने विश्वस्त ग्राहक हैं। "
            f"₹{tot_retail:g} के कुल बिल पर हमने ₹{friendly_discount:g} की विशेष किराना छूट कर दी है! "
            f"अब आपका कुल बिल केवल ₹{negotiated_total:g} हुआ। पैक कर दूँ?"
        )
        en_speech = (
            f"Arre {customer_name}! You are our long-time valued patron. "
            f"On your total bill of ₹{tot_retail:g}, we have applied a special kirana loyalty discount of ₹{friendly_discount:g}! "
            f"Your negotiated total is now ₹{negotiated_total:g}. Shall I pack it?"
        )

        return BhaavTaalResponse(
            is_bargain_intent=True,
            customer_name=customer_name,
            loyalty_tier=loyalty_tier,
            original_total_inr=round(tot_retail, 2),
            negotiated_total_inr=negotiated_total,
            total_savings_inr=friendly_discount,
            discount_pct=effective_disc_pct,
            merchant_margin_preserved_pct=preserved_margin_pct,
            spoken_counter_offer_hi=hi_speech,
            spoken_counter_offer_en=en_speech,
            bargain_items=bargain_details
        )

    def decompose_recipe_to_cart(
        self,
        dish_query: str,
        servings: int = 4,
        include_seasonings: bool = True
    ) -> RecipeToCartResponse:
        """
        'Rasoi se Rashan' (रसोई से राशन) Meal Recipe to Cart Decomposer:
        Maps colloquial Indian recipe requests (e.g. 'Rajma Chawal for 4 people') into optimal 35-SKU catalog staples,
        calculates portion scaling, bundles items with a combo meal discount, and crafts a spoken prompt.
        """
        q_lower = dish_query.lower()
        recipe_key = "rajma chawal"
        if "dal" in q_lower or "tadka" in q_lower or "दाल" in q_lower:
            recipe_key = "dal tadka"
        elif "chai" in q_lower or "tea" in q_lower or "nashta" in q_lower or "चाय" in q_lower:
            recipe_key = "chai nashta"
        elif "poha" in q_lower or "पोहा" in q_lower:
            recipe_key = "poha nashta"
        elif "paneer" in q_lower or "पनीर" in q_lower or "pulao" in q_lower:
            recipe_key = "paneer pulao"

        recipes_db = {
            "rajma chawal": {
                "name_en": "North Indian Rajma-Chawal Feast",
                "name_hi": "स्वादिष्ट पंजाबी राजमा-चावल कॉम्बो",
                "items": [
                    {"sku_id": "SKU-011", "qty": 1.0, "is_core": True},   # Chitra Rajma
                    {"sku_id": "SKU-002", "qty": 1.0, "is_core": True},   # Basmati Rice
                    {"sku_id": "SKU-022", "qty": 1.0, "is_core": False},  # MDH Degi Mirch
                    {"sku_id": "SKU-021", "qty": 1.0, "is_core": False},  # MDH Haldi
                    {"sku_id": "SKU-019", "qty": 1.0, "is_core": False},  # Tata Salt
                    {"sku_id": "SKU-017", "qty": 1.0, "is_core": False},  # Arogyam Mustard Oil
                ],
                "discount_pct": 5.0,
                "hi_base": "4 लोगों के राजमा-चावल के लिए चित्रा राजमा, बासमती चावल और आवश्यक मसाले कॉम्बो छूट के साथ कार्ट में जोड़ दिए हैं।"
            },
            "dal tadka": {
                "name_en": "Dhaba Style Dal Tadka & Rice",
                "name_hi": "ढाबा स्टाइल दाल तड़का और चावल",
                "items": [
                    {"sku_id": "SKU-007", "qty": 1.0, "is_core": True},   # Toor Dal
                    {"sku_id": "SKU-003", "qty": 1.0, "is_core": True},   # Sona Masoori Rice
                    {"sku_id": "SKU-018", "qty": 1.0, "is_core": False},  # Amul Pure Cow Ghee
                    {"sku_id": "SKU-021", "qty": 1.0, "is_core": False},  # MDH Haldi
                    {"sku_id": "SKU-019", "qty": 1.0, "is_core": False},  # Tata Salt
                ],
                "discount_pct": 5.0,
                "hi_base": "दाल-तड़का और चावल के लिए तूर दाल, सोना मसूरी चावल और अमूल शुद्ध घी कार्ट में जोड़ दिया गया है।"
            },
            "chai nashta": {
                "name_en": "Morning Chai-Nashta Breakfast Combo",
                "name_hi": "सुबह का चाय-नाश्ता कॉम्बो",
                "items": [
                    {"sku_id": "SKU-024", "qty": 1.0, "is_core": True},   # Red Label Tea
                    {"sku_id": "SKU-020", "qty": 1.0, "is_core": True},   # Madhur Sugar
                    {"sku_id": "SKU-012", "qty": 1.0, "is_core": True},   # Amul Taaza Milk
                    {"sku_id": "SKU-031", "qty": 2.0, "is_core": True},   # Parle-G Biscuit
                ],
                "discount_pct": 6.0,
                "hi_base": "चाय-नाश्ता के लिए रेड लेबल चाय, चीनी, ताज़ा दूध और 2 पैकेट पारले-जी बिस्कुट जोड़ दिए गए हैं।"
            },
            "poha nashta": {
                "name_en": "Indori Poha Breakfast Pack",
                "name_hi": "स्वादिष्ट इंदौरी पोहा नाश्ता पैक",
                "items": [
                    {"sku_id": "SKU-006", "qty": 1.0, "is_core": True},   # Tata Sampann Poha
                    {"sku_id": "SKU-016", "qty": 1.0, "is_core": True},   # Fortune Sunflower Oil
                    {"sku_id": "SKU-021", "qty": 1.0, "is_core": False},  # MDH Haldi
                    {"sku_id": "SKU-019", "qty": 1.0, "is_core": False},  # Tata Salt
                ],
                "discount_pct": 5.0,
                "hi_base": "पोहा नाश्ते के लिए 1 किलो टाटा पोहा, रिफाइंड तेल और हल्दी-नमक कार्ट में जोड़ दिए हैं।"
            },
            "paneer pulao": {
                "name_en": "Shahi Paneer Pulao Treat",
                "name_hi": "शाही पनीर पुलाव दावत",
                "items": [
                    {"sku_id": "SKU-014", "qty": 2.0, "is_core": True},   # Amul Malai Paneer
                    {"sku_id": "SKU-002", "qty": 1.0, "is_core": True},   # India Gate Basmati
                    {"sku_id": "SKU-018", "qty": 1.0, "is_core": False},  # Amul Pure Cow Ghee
                    {"sku_id": "SKU-022", "qty": 1.0, "is_core": False},  # MDH Degi Mirch
                ],
                "discount_pct": 6.0,
                "hi_base": "शाही पनीर पुलाव के लिए 2 पैकेट अमूल पनीर, बासमती चावल और देसी घी कॉम्बो में जोड़ दिए हैं।"
            }
        }

        entry = recipes_db[recipe_key]
        scale = max(0.5, round(servings / 4.0, 1))

        matched_items: List[RecipeIngredientItem] = []
        subtotal = 0.0

        for it in entry["items"]:
            if not include_seasonings and not it["is_core"]:
                continue
            sku = self.sku_lookup.get(it["sku_id"])
            if not sku:
                continue

            scaled_qty = round(it["qty"] * scale, 2)
            if scaled_qty < 1.0 and sku.unit == "packet":
                scaled_qty = 1.0

            line_cost = round(sku.price_inr * scaled_qty, 2)
            subtotal += line_cost

            matched_items.append(RecipeIngredientItem(
                sku_id=sku.sku_id,
                name_en=sku.name_en,
                name_hi=sku.name_hi,
                category=sku.category,
                quantity=scaled_qty,
                unit=sku.unit,
                price_inr=sku.price_inr,
                is_core_staple=it["is_core"],
                in_stock=getattr(sku, "in_stock", True)
            ))

        disc_pct = entry["discount_pct"]
        disc_amt = round(subtotal * (disc_pct / 100.0), 2)
        final_tot = round(subtotal - disc_amt, 2)

        hi_speech = f"{entry['hi_base']} कॉम्बो में {disc_pct}% छूट के साथ कुल बिल ₹{final_tot:g} हुआ। क्या तेल-मसाले घर पर हैं या वो भी जोड़ लें?"
        en_speech = f"Added ingredients for {entry['name_en']} ({servings} servings) with {disc_pct}% combo discount. Total is ₹{final_tot:g}."

        return RecipeToCartResponse(
            dish_name_en=entry["name_en"],
            dish_name_hi=entry["name_hi"],
            servings=servings,
            matched_ingredients=matched_items,
            bundle_subtotal_inr=round(subtotal, 2),
            bundle_discount_inr=disc_amt,
            bundle_total_inr=final_tot,
            spoken_recipe_prompt_hi=hi_speech,
            spoken_recipe_prompt_en=en_speech
        )


# Default singleton instance
catalogue_matcher = CatalogueMatcher()
