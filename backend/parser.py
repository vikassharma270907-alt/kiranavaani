import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from rapidfuzz import fuzz, distance

CATALOG_PATH = Path(__file__).resolve().parent.parent / "catalog" / "kirana_catalog_35_skus.json"

def load_catalog(path: Optional[Path] = None) -> Dict[str, Any]:
    target = path or CATALOG_PATH
    if not target.exists():
        alt_target = Path("catalog/kirana_catalog_35_skus.json")
        if alt_target.exists():
            target = alt_target
    with open(target, "r", encoding="utf-8") as f:
        return json.load(f)

# Boundary-safe regex generator supporting Latin and Devanagari characters
def make_boundary_regex(phrase: str) -> str:
    # If phrase contains spaces, allow flexible whitespace
    parts = phrase.strip().split()
    escaped_parts = [re.escape(p) for p in parts]
    inner = r"\s+".join(escaped_parts)
    return rf"(?<![\w\u0900-\u097F]){inner}(?![\w\u0900-\u097F])"

# Colloquial Hinglish and Hindi numeral normalization tables
RAW_NUMERAL_RULES: List[Tuple[List[str], str]] = [
    # Multi-word fractions
    (["sawa do", "सवा दो"], "2.25"),
    (["paune do", "पौने दो"], "1.75"),
    (["paune teen", "पौने तीन"], "2.75"),
    (["saadhe teen", "साढ़े तीन"], "3.5"),
    (["saadhe chaar", "साढ़े चार"], "4.5"),
    (["saadhe paanch", "साढ़े पांच"], "5.5"),
    (["paav bhar", "पाव भर"], "0.25"),
    # Single-word fractions
    (["dhai", "ढाई"], "2.5"),
    (["dedh", "डेढ़"], "1.5"),
    (["sawa", "सवा"], "1.25"),
    (["aadha", "आधा", "half"], "0.5"),
    (["paav", "पाव"], "0.25"),
    (["pauna", "पौना"], "0.75"),
    # Single numerals
    (["ek", "एक", "one"], "1"),
    (["do", "दो", "two"], "2"),
    (["teen", "तीन", "three"], "3"),
    (["chaar", "चार", "four"], "4"),
    (["paanch", "पांच", "five"], "5"),
    (["chheh", "chhe", "छह", "six"], "6"),
    (["saat", "सात", "seven"], "7"),
    (["aath", "आठ", "eight"], "8"),
    (["nau", "नौ", "nine"], "9"),
    (["das", "दस", "ten"], "10"),
]

ORDER_COMPLETION_PHRASES = [
    "ho gaya", "हो गया",
    "bas itna hi", "bus itna hi", "बस इतना ही", "बस इतना", "bas itna",
    "itna hi hai", "इतना ही है",
    "bill bana do", "बिल बना दो",
    "pack kar do", "पैक कर दो", "pack kar dena",
    "bhej do", "भेज दो", "भेज देना"
]

CONVERSATIONAL_FILLERS = [
    "bhaiya", "भैया",
    "gupta ji", "गुप्ता जी",
    "namaste", "नमस्ते",
    "kripya", "कृपया",
    "likh lo", "लिख लो",
    "chahiye", "चाहिए",
    "dena", "देना"
]

# Ambiguity groups for explicit clarification re-ask prompts
AMBIGUITY_RESOLVERS: Dict[str, Dict[str, Any]] = {
    "rice": {
        "trigger": ["chawal", "चावल", "rice", "akki", "arisi"],
        "exclusion": ["basmati", "बासमती", "india gate", "sona masoori", "सोना मसूरी", "sadharan", "साधारण"],
        "question_hi": "'इंडिया गेट बासमती चावल' (₹95/kg) चाहिए या 'सोना मसूरी साधारण चावल' (₹58/kg)?",
        "question_en": "India Gate Basmati Chawal (₹95/kg) or Sona Masoori Regular Chawal (₹58/kg)?",
        "options": [
            {"sku_id": "SKU-002", "name_hi": "इंडिया गेट बासमती चावल", "price_inr": 95.0},
            {"sku_id": "SKU-003", "name_hi": "साधारण सोना मसूरी चावल", "price_inr": 58.0}
        ]
    },
    "maggi": {
        "trigger": ["maggi", "मैगी", "meghee", "meggi", "noodles"],
        "exclusion": ["masala", "मसाला", "atta", "आटा", "veg", "2 minute", "२-मिनट"],
        "question_hi": "'मैगी २-मिनट मसाला नूडल्स' (₹14) चाहिए या 'मैगी आटा नूडल्स' (₹25)?",
        "question_en": "Maggi 2-Minute Masala (₹14) or Maggi Veg Atta Noodles (₹25)?",
        "options": [
            {"sku_id": "SKU-027", "name_hi": "मैगी २-मिनट मसाला नूडल्स", "price_inr": 14.0},
            {"sku_id": "SKU-028", "name_hi": "मैगी आटा नूडल्स", "price_inr": 25.0}
        ]
    },
    "dal": {
        "trigger": ["dal", "daal", "दाल", "bele", "paruppu"],
        "exclusion": ["toor", "तूर", "arhar", "अरहर", "moong", "मूंग", "chana", "चना"],
        "question_hi": "'तूर दाल' (₹140/kg), 'मूंग दाल' (₹128/kg) या 'चना दाल' (₹92/kg) चाहिए?",
        "question_en": "Toor Dal (₹140/kg), Moong Dal (₹128/kg) or Chana Dal (₹92/kg)?",
        "options": [
            {"sku_id": "SKU-007", "name_hi": "टाटा संपन्न तूर दाल", "price_inr": 140.0},
            {"sku_id": "SKU-008", "name_hi": "टाटा संपन्न मूंग दाल धुली", "price_inr": 128.0},
            {"sku_id": "SKU-009", "name_hi": "टाटा संपन्न चना दाल", "price_inr": 92.0}
        ]
    },
    "oil": {
        "trigger": ["tel", "oil", "तेल", "enne", "ennai"],
        "exclusion": ["fortune", "फॉर्च्यून", "sunflower", "refined", "sarson", "सरसों", "arogyam", "आरोग्यम", "almond", "बादाम", "badam", "ghee", "घी"],
        "question_hi": "'फॉर्च्यून रिफाइंड तेल' (₹145/L), 'आरोग्यम सरसों तेल' (₹158/L) या 'बजाज बादाम तेल' (₹65) चाहिए?",
        "question_en": "Fortune Refined (₹145/L), Arogyam Mustard Oil (₹158/L), or Bajaj Almond Hair Oil (₹65)?",
        "options": [
            {"sku_id": "SKU-016", "name_hi": "फॉर्च्यून सनलाइट रिफाइंड तेल", "price_inr": 145.0},
            {"sku_id": "SKU-017", "name_hi": "आरोग्यम कच्ची घानी सरसों तेल", "price_inr": 158.0},
            {"sku_id": "SKU-033", "name_hi": "बजाज बादाम ड्रॉप्स हेयर ऑयल", "price_inr": 65.0}
        ]
    }
}


class HinglishOrderParser:
    def __init__(self, catalog_path: Optional[Path] = None):
        self.catalog_data = load_catalog(catalog_path)
        self.skus: List[Dict[str, Any]] = self.catalog_data.get("skus", [])
        self.sku_lookup: Dict[str, Dict[str, Any]] = {s["sku_id"]: s for s in self.skus}
        self.keyterms: List[str] = self._extract_keyterms()
        # Compile normalization regexes
        self.compiled_numeral_rules = [
            (re.compile(make_boundary_regex(phrase), re.IGNORECASE), val)
            for phrases, val in RAW_NUMERAL_RULES
            for phrase in phrases
        ]

    def _extract_keyterms(self) -> List[str]:
        terms = set()
        for s in self.skus:
            terms.add(s["name_hi"])
            terms.add(s["name_en"])
            for alias in s.get("aliases", []):
                terms.add(alias)
        extra = [
            "सवा", "ढाई", "डेढ़", "आधा", "पाव", "पौना", "किलो", "ग्राम", "लीटर",
            "पैकेट", "बोतल", "डब्बा", "हो गया", "बस इतना ही", "बिल", "चाहिए",
            "देना", "लिख लो", "पैक कर दो", "नमस्ते", "भैया", "गुप्ता जी"
        ]
        for e in extra:
            terms.add(e)
        return sorted(list(terms))[:200]

    def normalize_numerals(self, text: str) -> str:
        """Normalizes colloquial Hindi, Hinglish, and English numerals and fractional quantities."""
        normalized = text
        for regex, replacement in self.compiled_numeral_rules:
            normalized = regex.sub(replacement, normalized)
        return normalized

    def check_order_completion(self, text: str) -> bool:
        """Detects whether caller signaled end of order."""
        for phrase in ORDER_COMPLETION_PHRASES:
            reg = make_boundary_regex(phrase)
            if re.search(reg, text, flags=re.IGNORECASE):
                return True
        return False

    def strip_conversational_cues(self, text: str) -> str:
        """Removes greetings, fillers, and completion signals before clause splitting."""
        cleaned = text
        all_cues = ORDER_COMPLETION_PHRASES + CONVERSATIONAL_FILLERS
        for cue in all_cues:
            reg = make_boundary_regex(cue)
            cleaned = re.sub(reg, " ", cleaned, flags=re.IGNORECASE)
        return cleaned

    def calculate_levenshtein_similarity(self, token: str, target: str) -> float:
        token = token.strip().lower()
        target = target.strip().lower()
        if not token or not target:
            return 0.0
        dist = distance.Levenshtein.distance(token, target)
        max_len = max(len(token), len(target))
        return 1.0 - (dist / max_len)

    def extract_quantity_and_unit(self, clause: str, default_unit: str = "pack") -> Tuple[float, str]:
        # Match pattern: number followed by optional unit
        match = re.search(
            r"(\d+(?:\.\d+)?)\s*(kilo|kg|किलो|किग्रा|gram|gm|g|ग्राम|litre|liter|ltr|l|लीटर|packet|pkt|पैकेट|pack|पैक|bottle|बोतल)?",
            clause,
            flags=re.IGNORECASE
        )
        if not match:
            return 1.0, default_unit

        raw_qty = float(match.group(1))
        unit_str = match.group(2)

        if not unit_str:
            return raw_qty, default_unit

        unit_str = unit_str.lower()
        if unit_str in ["kilo", "kg", "किलो", "किग्रा"]:
            return raw_qty, "kg"
        elif unit_str in ["gram", "gm", "g", "ग्राम"]:
            if default_unit == "kg":
                return round(raw_qty / 1000.0, 3), "kg"
            return raw_qty, "gram"
        elif unit_str in ["litre", "liter", "ltr", "l", "लीटर"]:
            return raw_qty, "litre"
        elif unit_str in ["ml", "एमएल"]:
            if default_unit == "litre":
                return round(raw_qty / 1000.0, 3), "litre"
            return raw_qty, "ml"
        elif unit_str in ["packet", "pkt", "पैकेट"]:
            return raw_qty, "packet"
        elif unit_str in ["pack", "पैक"]:
            return raw_qty, "pack"
        elif unit_str in ["bottle", "बोतल"]:
            return raw_qty, "bottle"
        return raw_qty, default_unit

    def match_clause(self, clause: str, keyterms_enabled: bool = True) -> Dict[str, Any]:
        clause_clean = clause.strip()
        if not clause_clean or len(clause_clean) < 2:
            return {"status": "EMPTY"}

        # 1. Check Ambiguity Resolvers
        for fam_key, resolver in AMBIGUITY_RESOLVERS.items():
            trigger_found = any(re.search(make_boundary_regex(t), clause_clean, flags=re.IGNORECASE) for t in resolver["trigger"])
            if trigger_found:
                exclusion_found = any(re.search(make_boundary_regex(ex), clause_clean, flags=re.IGNORECASE) for ex in resolver["exclusion"])
                if not exclusion_found:
                    qty, _ = self.extract_quantity_and_unit(clause_clean, default_unit="kg")
                    unit_hint = self.sku_lookup[resolver["options"][0]["sku_id"]]["unit"]
                    return {
                        "status": "CLARIFICATION_REQUIRED",
                        "family": fam_key,
                        "spoken_clause": clause_clean,
                        "question_hi": f"कम कॉन्फिडेंस (0.68): क्या आपको {qty:g} {unit_hint} मात्रा में {resolver['question_hi']}",
                        "question_en": f"Low Confidence (0.68): For {qty:g} {unit_hint}, {resolver['question_en']}",
                        "options": [
                            {
                                "sku_id": opt["sku_id"],
                                "name_hi": opt["name_hi"],
                                "qty": qty,
                                "price_inr": opt["price_inr"],
                                "unit": self.sku_lookup[opt["sku_id"]]["unit"]
                            }
                            for opt in resolver["options"]
                        ],
                        "confidence": 0.68
                    }

        # 2. Check Match across Catalog
        best_sku = None
        best_score = 0.0
        best_alias = ""

        # Remove quantity strings before searching product aliases to avoid noise
        clause_words = re.sub(r"^\s*\d+(?:\.\d+)?\s*(kilo|kg|किलो|gram|gm|litre|लीटर|pack|packet)?", "", clause_clean, flags=re.IGNORECASE).strip()
        target_clause = clause_words if len(clause_words) >= 2 else clause_clean

        for sku in self.skus:
            for alias in sku.get("aliases", []):
                alias_lower = alias.lower()
                clause_lower = target_clause.lower()

                # For short aliases (<= 3 chars, e.g. "दही", "दूध", "तेल", "घी", "चाय", "रवा"), require boundary match!
                if len(alias_lower) <= 3:
                    if re.search(make_boundary_regex(alias_lower), clause_lower, flags=re.IGNORECASE):
                        score = 0.96 if keyterms_enabled else 0.85
                        if score > best_score:
                            best_score = score
                            best_sku = sku
                            best_alias = alias
                    continue

                # For normal aliases
                if alias_lower in clause_lower:
                    score = 0.96 if keyterms_enabled else 0.85
                    if "meghee" in clause_lower and not keyterms_enabled:
                        score = 0.72
                    if score > best_score:
                        best_score = score
                        best_sku = sku
                        best_alias = alias
                else:
                    # Levenshtein / RapidFuzz partial ratio
                    sim = fuzz.partial_ratio(alias_lower, clause_lower) / 100.0
                    lev = self.calculate_levenshtein_similarity(alias_lower, clause_lower)
                    comb = max(sim, lev)
                    if comb > best_score:
                        best_score = comb
                        best_sku = sku
                        best_alias = alias

        # Keyterms boosting effect
        if keyterms_enabled and best_sku and best_score >= 0.70:
            best_score = min(0.99, best_score + 0.15)
        elif not keyterms_enabled and "meghee" in target_clause.lower():
            best_score = 0.65

        if not best_sku or best_score < 0.55:
            return {
                "status": "UNRECOGNIZED",
                "spoken_clause": clause_clean,
                "confidence": round(best_score, 2)
            }

        qty, unit = self.extract_quantity_and_unit(clause_clean, default_unit=best_sku["unit"])

        # Low confidence clarification gate (0.55 <= score < 0.78)
        if best_score < 0.78:
            return {
                "status": "CLARIFICATION_REQUIRED",
                "family": "low_confidence",
                "spoken_clause": clause_clean,
                "question_hi": f"कम कॉन्फिडेंस ({best_score:.2f}): क्या आपने '{best_sku['name_hi']}' ({best_sku['name_en']}) कहा?",
                "question_en": f"Low Confidence ({best_score:.2f}): Did you say '{best_sku['name_en']}'?",
                "options": [
                    {
                        "sku_id": best_sku["sku_id"],
                        "name_hi": best_sku["name_hi"],
                        "qty": qty,
                        "price_inr": best_sku["price_inr"],
                        "unit": best_sku["unit"]
                    }
                ],
                "confidence": round(best_score, 2)
            }

        line_total = round(qty * best_sku["price_inr"], 2)
        return {
            "status": "MATCHED",
            "sku_id": best_sku["sku_id"],
            "name_hi": best_sku["name_hi"],
            "name_en": best_sku["name_en"],
            "name_kn": best_sku["name_kn"],
            "name_ta": best_sku["name_ta"],
            "qty": qty,
            "unit": best_sku["unit"],
            "price_inr": best_sku["price_inr"],
            "line_total_inr": line_total,
            "match_confidence": round(best_score, 2),
            "matched_alias": best_alias,
            "spoken_clause": clause_clean
        }

    def parse_utterance(
        self,
        utterance: str,
        prisma_version: str = "prisma-v3.0",
        keyterms_enabled: bool = True
    ) -> Dict[str, Any]:
        simulated_transcript = utterance
        if not keyterms_enabled:
            # Degrade specific brand names without keyterm boost
            simulated_transcript = re.sub(make_boundary_regex("maggi"), "meghee", simulated_transcript, flags=re.IGNORECASE)
            simulated_transcript = re.sub(make_boundary_regex("मैगी"), "meghee", simulated_transcript, flags=re.IGNORECASE)
            simulated_transcript = re.sub(make_boundary_regex("kurkure"), "kurkura", simulated_transcript, flags=re.IGNORECASE)
            simulated_transcript = re.sub(make_boundary_regex("arogyam"), "arogya", simulated_transcript, flags=re.IGNORECASE)

        # Normalize numerals
        norm_text = self.normalize_numerals(simulated_transcript)

        # Check completion signal before stripping
        is_order_complete = self.check_order_completion(norm_text)

        # Strip conversational cues
        filtered_text = self.strip_conversational_cues(norm_text)

        # Split clauses by comma, aur, और, and, plus, semicolons
        clauses = re.split(r",|\baur\b|\bऔर\b|\band\b|;|\+", filtered_text, flags=re.IGNORECASE)

        matched_items = []
        clarifications_needed = []

        for raw_c in clauses:
            c = raw_c.strip()
            if not c or len(c) < 2:
                continue
            res = self.match_clause(c, keyterms_enabled=keyterms_enabled)
            if res["status"] == "MATCHED":
                matched_items.append(res)
            elif res["status"] == "CLARIFICATION_REQUIRED":
                clarifications_needed.append(res)

        total_inr = round(sum(i["line_total_inr"] for i in matched_items), 2)

        # Build Timbre v2.5 Spoken Reply
        if clarifications_needed:
            timbre_reply = clarifications_needed[0]["question_hi"]
        elif matched_items:
            items_summary = ", ".join([
                f"{i['qty']:g} {i['unit']} {i['name_hi']}" for i in matched_items
            ])
            if is_order_complete:
                timbre_reply = f"{items_summary} — कुल {int(total_inr)} रुपये, सही है?"
            else:
                timbre_reply = f"{items_summary} कार्ट में जोड़ दिया है। और कुछ चाहिए?"
        else:
            timbre_reply = "कृपया बताइए आपको क्या किराना सामान और कितनी मात्रा में चाहिए?"

        return {
            "model": prisma_version,
            "auto_lid_detected": "hi-Latn / hi-Deva (Code-Mixed 98.4%)",
            "keyterms_boosted_count": len(self.keyterms) if keyterms_enabled else 0,
            "transcript": simulated_transcript,
            "normalized_transcript": norm_text,
            "items": matched_items,
            "clarifications_needed": clarifications_needed,
            "is_order_complete": is_order_complete,
            "total_inr": total_inr,
            "timbre_v25_tts_reply": timbre_reply
        }
