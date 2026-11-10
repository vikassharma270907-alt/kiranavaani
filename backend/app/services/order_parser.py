"""
Hinglish Order Parser Module.
Extracts product mentions, quantities, and units from code-mixed Hindi-English speech transcripts.
Normalizes colloquial fractional numerals ('aadha' -> 0.5, 'dhai' -> 2.5, 'dedh' -> 1.5, 'sawa do' -> 2.25).
"""
import re
from typing import List, Tuple, Dict, Any, Optional

from backend.app.schemas import ParsedItem, ParseOrderResponse


def make_boundary_regex(phrase: str) -> str:
    """Boundary-safe regex pattern supporting Latin and Devanagari characters."""
    parts = phrase.strip().split()
    escaped = [re.escape(p) for p in parts]
    inner = r"\s+".join(escaped)
    return rf"(?<![\w\u0900-\u097F]){inner}(?![\w\u0900-\u097F])"


# Comprehensive Hinglish / Hindi numeral normalization table
NUMERAL_RULES: List[Tuple[List[str], str]] = [
    # Multi-word fractions
    (["sawa do", "सवा दो"], "2.25"),
    (["paune do", "पौने दो"], "1.75"),
    (["paune teen", "पौने तीन"], "2.75"),
    (["saadhe teen", "साढ़े तीन", "sadhe teen"], "3.5"),
    (["saadhe chaar", "साढ़े चार", "sadhe chaar"], "4.5"),
    (["saadhe paanch", "साढ़े पांच", "sadhe paanch"], "5.5"),
    (["paav bhar", "पाव भर", "pao bhar"], "0.25"),

    # Single-word fractions
    (["dhai", "ढाई", "dhaai"], "2.5"),
    (["dedh", "डेढ़", "deydh"], "1.5"),
    (["sawa", "सवा"], "1.25"),
    (["aadha", "आधा", "aadhe", "adha", "half"], "0.5"),
    (["paav", "पाव", "pao"], "0.25"),
    (["pauna", "पौना", "paun"], "0.75"),

    # Cardinal numerals
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
    (["gyarah", "ग्यारह", "eleven"], "11"),
    (["barah", "बारह", "twelve"], "12"),
    (["pandrah", "पंद्रह", "fifteen"], "15"),
    (["bees", "बीस", "twenty"], "20"),
    (["pachees", "पच्चीस", "twenty five"], "25"),
    (["pachaas", "पचास", "fifty"], "50"),
    (["sau", "सौ", "hundred"], "100"),
]

ORDER_COMPLETION_PHRASES = [
    "ho gaya", "हो गया",
    "bas itna hi", "bus itna hi", "बस इतना ही", "बस इतना", "bas itna",
    "itna hi hai", "इतना ही है",
    "bill bana do", "बिल बना दो",
    "pack kar do", "पैक कर दो", "pack kar dena",
    "bhej do", "भेज दो", "भेज देना", "bhej dena"
]

CONVERSATIONAL_FILLERS = [
    "bhaiya", "भैया",
    "gupta ji", "गुप्ता जी",
    "namaste", "नमस्ते",
    "kripya", "कृपया",
    "likh lo", "लिख लो",
    "chahiye", "चाहिए",
    "dena", "देना",
    "dijiye", "दीजिए",
    "please", "zarra"
]

UNIT_NORMALIZATION_MAP: Dict[str, str] = {
    # Weight
    "kg": "kg", "kilo": "kg", "kilos": "kg", "किलो": "kg", "किग्रा": "kg", "kilogram": "kg",
    "gm": "gram", "gram": "gram", "grams": "gram", "g": "gram", "ग्राम": "gram",
    # Volume
    "litre": "litre", "liter": "litre", "litres": "litre", "ltr": "litre", "l": "litre", "लीटर": "litre",
    "ml": "ml", "मिली": "ml",
    # Packaging
    "packet": "packet", "pkt": "packet", "packets": "packet", "पैकेट": "packet",
    "pack": "pack", "packs": "pack", "पैक": "pack",
    "bottle": "bottle", "botal": "bottle", "बोतल": "bottle",
    "dabba": "box", "box": "box", "डब्बा": "box",
    "piece": "piece", "pc": "piece", "pcs": "piece", "पीस": "piece", "टुकड़ा": "piece"
}


class HinglishOrderParser:
    def __init__(self):
        # Precompile numeral replacement rules
        self.compiled_numeral_rules = [
            (re.compile(make_boundary_regex(phrase), re.IGNORECASE), val)
            for phrases, val in NUMERAL_RULES
            for phrase in phrases
        ]

    def normalize_numerals(self, text: str) -> str:
        """Converts Hindi and Hinglish numbers into Arabic numerals (e.g., 'dhai' -> '2.5')."""
        normalized = text
        for regex, val in self.compiled_numeral_rules:
            normalized = regex.sub(val, normalized)
        return normalized

    def check_order_completion(self, text: str) -> bool:
        """Checks if the speaker indicated order completion (e.g., 'bas itna hi')."""
        for phrase in ORDER_COMPLETION_PHRASES:
            reg = make_boundary_regex(phrase)
            if re.search(reg, text, flags=re.IGNORECASE):
                return True
        return False

    def strip_conversational_fillers(self, text: str) -> str:
        """Removes greetings and polite fillers to isolate product order clauses."""
        cleaned = text
        all_cues = ORDER_COMPLETION_PHRASES + CONVERSATIONAL_FILLERS
        for cue in all_cues:
            reg = make_boundary_regex(cue)
            cleaned = re.sub(reg, " ", cleaned, flags=re.IGNORECASE)
        # Collapse multi spaces
        return re.sub(r"\s+", " ", cleaned).strip()

    def extract_quantity_and_unit(self, clause: str, default_unit: str = "packet") -> Tuple[float, str, str]:
        """
        Extracts quantity number, unit, and the remaining product string from a clause.
        Returns: (quantity, unit, product_text)
        """
        # Look for: digits/decimal followed by optional unit
        unit_pattern = r"(kilo|kg|kilos|किलो|किग्रा|kilogram|gram|gm|grams|g|ग्राम|litre|liter|ltr|litres|l|लीटर|ml|मिली|packet|pkt|packets|पैकेट|pack|packs|पैक|bottle|botal|बोतल|dabba|box|डब्बा|piece|pc|pcs|पीस)?"
        match = re.search(
            rf"(\d+(?:\.\d+)?)\s*{unit_pattern}",
            clause,
            flags=re.IGNORECASE
        )

        if not match:
            # No explicit quantity found; default to 1.0
            return 1.0, default_unit, clause.strip()

        raw_qty = float(match.group(1))
        raw_unit = match.group(2)
        unit = default_unit

        if raw_unit:
            raw_unit_lower = raw_unit.lower()
            unit = UNIT_NORMALIZATION_MAP.get(raw_unit_lower, default_unit)

        # Remove the matched quantity and unit substring to get remaining product text
        product_text = clause[:match.start()] + " " + clause[match.end():]
        # Clean punctuation and extra whitespace
        product_text = re.sub(r"[^\w\s\u0900-\u097F\-]", " ", product_text)
        product_text = re.sub(r"\s+", " ", product_text).strip()

        return raw_qty, unit, product_text

    def parse_utterance(self, text: str, keyterms_enabled: bool = True) -> ParseOrderResponse:
        """
        Parses a full transcript into individual product mentions with normalized quantity and unit.
        """
        raw_transcript = text.strip()
        is_order_complete = self.check_order_completion(raw_transcript)
        
        # 1. First strip conversational fillers and completion verbs from raw text
        # (This prevents verbs like 'pack kar do' from having 'do' converted to '2')
        cleaned_text = self.strip_conversational_fillers(raw_transcript)
        
        # 2. Normalize numerals in cleaned text and generate full normalized transcript
        cleaned_normalized = self.normalize_numerals(cleaned_text)
        normalized_transcript = self.normalize_numerals(raw_transcript)

        # 3. Split clauses by delimiters
        clauses = re.split(r",|\baur\b|\bऔर\b|\band\b|\btatha\b|\bतथा\b|;|\+|&|\bsaath me\b|\bसाथ में\b", cleaned_normalized, flags=re.IGNORECASE)

        items: List[ParsedItem] = []
        for raw_c in clauses:
            clause = raw_c.strip()
            if not clause or len(clause) < 2:
                continue

            # Check if this clause is purely a filler or completion word that escaped
            if clause.lower() in ("bhej dena", "pack kar do", "itna hi", "likh lo", "dena"):
                continue

            qty, unit, prod_text = self.extract_quantity_and_unit(clause)

            # If prod_text is empty, try to see if original clause had product
            final_prod = prod_text if prod_text else clause

            items.append(
                ParsedItem(
                    product=final_prod,
                    quantity=qty,
                    unit=unit,
                    raw_clause=clause
                )
            )

        return ParseOrderResponse(
            raw_transcript=raw_transcript,
            normalized_transcript=normalized_transcript,
            items=items,
            is_order_complete=is_order_complete
        )


# Default singleton instance
order_parser = HinglishOrderParser()
