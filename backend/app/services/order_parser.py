"""
Hinglish & Multi-Lingual Order Parser Module.
Extracts product mentions, quantities, units, and Kirana Khata (credit ledger) tags
from code-mixed Hindi, English, Kannada, and Tamil speech transcripts.
Normalizes colloquial fractional numerals ('aadha' -> 0.5, 'dhai' -> 2.5, 'dedh' -> 1.5,
'sawa do' -> 2.25, 'paav bhar' -> 0.25, 'ondavare' -> 1.5, 'eradavare' -> 2.5).
"""
import re
from typing import List, Tuple, Dict, Any, Optional

from backend.app.schemas import ParsedItem, ParseOrderResponse, KhataInfo, RepairedItemEvent, DeliveryLandmarkInfo, CustomerJazbaatInfo


def make_boundary_regex(phrase: str) -> str:
    """Boundary-safe regex pattern supporting Latin, Devanagari, Kannada, and Tamil characters."""
    parts = phrase.strip().split()
    escaped = [re.escape(p) for p in parts]
    inner = r"\s+".join(escaped)
    word_chars = r"\w\u0900-\u0963\u0966-\u097F\u0C80-\u0CFF\u0B80-\u0BFF"
    return rf"(?<![{word_chars}]){inner}(?![{word_chars}])"


# Comprehensive Multilingual Indic Numeral Rules (Hindi, Hinglish, Kannada, Tamil)
NUMERAL_RULES: List[Tuple[List[str], str]] = [
    # Multi-word Hindi & Hinglish fractions
    (["sawa do", "सवा दो"], "2.25"),
    (["paune do", "पौने दो"], "1.75"),
    (["paune teen", "पौने तीन"], "2.75"),
    (["saadhe teen", "साढ़े तीन", "sadhe teen"], "3.5"),
    (["saadhe chaar", "साढ़े चार", "sadhe chaar"], "4.5"),
    (["saadhe paanch", "साढ़े पांच", "sadhe paanch"], "5.5"),
    (["ek paav", "एक पाव", "ek pao"], "0.25"),
    (["do paav", "दो पाव", "do pao"], "0.5"),
    (["aadha paav", "adha paav", "आधा पाव", "aadha pao"], "0.125"),
    (["dedh paav", "deydh paav", "डेढ़ पाव", "dedh pao"], "0.375"),
    (["sawa paav", "सवा पाव", "sawa pao"], "0.3125"),
    (["paav bhar", "पाव भर", "pao bhar", "paav", "पाव", "pao"], "0.25"),
    (["dedh darjan", "डेढ़ दर्जन"], "18"),
    (["aadha darjan", "आधा दर्जन", "half dozen"], "6"),
    (["darjan", "दर्जन", "dozen"], "12"),

    # Kannada Multi-word & Fractions
    (["ondavare", "ಒಂದೂವರೆ"], "1.5"),
    (["eradavare", "ಎರಡೂವರೆ"], "2.5"),
    (["mooruvare", "mooravare", "ಮೂರಾವರೆ"], "3.5"),
    (["ondu mukkaal", "ondmukkaal", "ಒಂದು ಮುಕ್ಕಾಲು"], "1.75"),
    (["mukkaal", "mukaalu", "ಮುಕ್ಕಾಲು"], "0.75"),
    (["ardha", "ಅರ್ಧ"], "0.5"),
    (["kaalu", "ಕಾಲು"], "0.25"),

    # Tamil Multi-word & Fractions
    (["ondrara", "ondrare", "ஒன்றரை"], "1.5"),
    (["rendara", "rendare", "இரண்டரை"], "2.5"),
    (["moonara", "moonare", "மூன்றரை"], "3.5"),
    (["mukkaal", "mukaal", "முக்கால்"], "0.75"),
    (["ara", "arai", "அரை"], "0.5"),
    (["kaal", "கால்"], "0.25"),

    # Single-word Hindi fractions
    (["dhai", "ढाई", "dhaai"], "2.5"),
    (["dedh", "डेढ़", "deydh"], "1.5"),
    (["sawa", "सवा"], "1.25"),
    (["aadha", "आधा", "aadhe", "adha", "half"], "0.5"),
    (["pauna", "पौना", "paun"], "0.75"),

    # Cardinal numerals (Hindi / English)
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

    # Cardinal numerals (Kannada)
    (["ondu", "ಒಂದು"], "1"),
    (["eradu", "ಎರಡು"], "2"),
    (["mooru", "ಮೂರು"], "3"),
    (["naalku", "ನಾಲ್ಕು"], "4"),
    (["aidu", "ಐದು"], "5"),
    (["aaru", "ಆರು"], "6"),
    (["elu", "ಏಳು"], "7"),
    (["entu", "ಎಂಟು"], "8"),
    (["ombattu", "ಒಂಬತ್ತು"], "9"),
    (["hattu", "ಹತ್ತು"], "10"),

    # Cardinal numerals (Tamil)
    (["oru", "onnu", "ஒன்று"], "1"),
    (["rendu", "இரண்டு"], "2"),
    (["moonu", "மூன்று"], "3"),
    (["naalu", "நான்கு"], "4"),
    (["anji", "aindhu", "ஐந்து"], "5"),
    (["aaru", "ஆறு"], "6"),
    (["ezhu", "ஏழு"], "7"),
    (["ettu", "எட்டு"], "8"),
    (["onbadhu", "ஒன்பது"], "9"),
    (["pathu", "பத்து"], "10"),
]

ORDER_COMPLETION_PHRASES = [
    # Hindi / Hinglish
    "ho gaya", "हो गया",
    "bas itna hi", "bus itna hi", "बस इतना ही", "बस इतना", "bas itna",
    "itna hi hai", "इतना ही है",
    "bill bana do", "बिल बना दो",
    "pack kar do", "पैक कर दो", "pack kar dena",
    "bhej do", "भेज दो", "भेज देना", "bhej dena",
    # Kannada
    "saaku", "ಸಾಕು",
    "aste", "ಅಷ್ಟೇ",
    "bega kodi", "ಬೇಗ ಕೊಡಿ",
    "eshtu aaythu", "ಎಷ್ಟು ಆಯ್ತು",
    "bill kodi", "ಬಿಲ್ ಕೊಡಿ",
    "pack maadi", "ಪ್ಯಾಕ್ ಮಾಡಿ",
    # Tamil
    "avlo dhaan", "அவ்வளவு தான்",
    "podhum", "போதும்",
    "bill podunga", "பில் போடுங்க",
    "pack pannunga", "பேக் பண்ணுங்க"
]

CONVERSATIONAL_FILLERS = [
    # Hindi / Hinglish
    "bhaiya", "भैया",
    "gupta ji", "गुप्ता जी",
    "namaste", "नमस्ते",
    "kripya", "कृपया",
    "likh lo", "लिख लो",
    "chahiye", "चाहिए",
    "dena", "देना",
    "dijiye", "दीजिए",
    "de do", "दे दो",
    "kar do", "कर दो",
    "de dena", "दे देना",
    "daal dena", "daal do", "daal dijiye",
    "डाल देना", "डाल दो", "डाल दीजिए",
    "please", "zarra",
    # Kannada
    "anna", "ಅಣ್ಣ",
    "kodi", "ಕೊಡಿ",
    "dayavittu", "ದಯವಿಟ್ಟು",
    "re",
    # Tamil
    "anna", "அண்ணா",
    "kudunga", "குடுங்க",
    "thambi", "தம்பி"
]

UNIT_NORMALIZATION_MAP: Dict[str, str] = {
    # Weight
    "kg": "kg", "kilo": "kg", "kilos": "kg", "किलो": "kg", "किग्रा": "kg", "kilogram": "kg",
    "gm": "gram", "gram": "gram", "grams": "gram", "g": "gram", "ग्राम": "gram",
    "paav": "kg", "pao": "kg", "पाव": "kg",
    # Volume
    "litre": "litre", "liter": "litre", "litres": "litre", "ltr": "litre", "l": "litre", "लीटर": "litre",
    "ml": "ml", "मिली": "ml",
    # Packaging & Pieces
    "packet": "packet", "pkt": "packet", "packets": "packet", "पैकेट": "packet",
    "pack": "pack", "packs": "pack", "पैक": "pack",
    "bottle": "bottle", "botal": "bottle", "बोतल": "bottle",
    "dabba": "box", "box": "box", "डब्बा": "box",
    "piece": "piece", "pc": "piece", "pcs": "piece", "पीस": "piece", "टुकड़ा": "piece",
    "darjan": "piece", "dozen": "piece", "दर्जन": "piece"
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
        """Removes greetings, polite fillers, and ledger phrases to isolate product order clauses."""
        cleaned = text
        # Normalize Devanagari danda and common sentence punctuation to spaces (preserve numeric decimals)
        cleaned = re.sub(r"(?<!\d)\.(?!\d)|[\u0964\u0965!?]", " ", cleaned)
        # Remove khata/ledger phrases from being falsely parsed as product names (e.g. 'Sharma ji ke khaate me likh lo')
        cleaned = re.sub(
            r"(?:[a-zA-Z\u0900-\u097F]+(?:\s+ji)?\s+)?ke\s+(?:khaate|khata|खाते|खाता)\s+(?:me|में)?(?:\s*(?:daal\s+dena|daal\s+do|likh\s+lo|likh\s+dena|डाल\s+देना|लिख\s+लो))?",
            " ",
            cleaned,
            flags=re.IGNORECASE
        )
        cleaned = re.sub(r"paise\s+.*?(?:dunga|denge|देंगे|दूंगा)", " ", cleaned, flags=re.IGNORECASE)

        # Remove bargaining and past memory expressions to prevent phantom grocery items (bounded lookaheads to avoid consuming subsequent order items)
        cleaned = re.sub(
            r"(?:kuch\s+(?:to\s+)?discount|thoda\s+discount|discount\s+lagao|chhoot\s+do|kam\s+karo|kuch\s+kam|कुछ\s+तो\s+डिस्काउंट|डिस्काउंट\s+लगाओ|छूट\s+दो|कम\s+करो|कम\s+लगाओ|डिस्काउंट|discount)(?:\s+(?:milega|dena|kya|bhaiya|gupta\s+ji|bhi))?",
            " ",
            cleaned,
            flags=re.IGNORECASE
        )
        cleaned = re.sub(
            r"(?:pichli\s+baar|पिछली\s+बार|last\s+time)(?:\s+(?:to|bhi|lagaya\s+tha|diya\s+tha))?",
            " ",
            cleaned,
            flags=re.IGNORECASE
        )

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
        unit_pattern = r"(kilo|kg|kilos|किलो|किग्रा|kilogram|gram|gm|grams|g|ग्राम|litre|liter|ltr|litres|l|लीटर|ml|मिली|packet|pkt|packets|पैकेट|pack|packs|पैक|bottle|botal|बोतल|dabba|box|डब्बा|piece|pc|pcs|पीस|darjan|dozen|दर्जन)?"
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
        # Clean punctuation and extra whitespace while preserving Devanagari, Kannada, and Tamil
        product_text = re.sub(r"[^\w\s\u0900-\u097F\u0C80-\u0CFF\u0B80-\u0BFF\-]", " ", product_text)
        product_text = re.sub(r"\s+", " ", product_text).strip()

        return raw_qty, unit, product_text

    def extract_khata_info(self, text: str) -> Optional[KhataInfo]:
        """
        Detects Kirana Khata (credit ledger) requests in Indian retail:
        e.g. 'Sharma ji ke khaate me likh lo', 'khata number 42', 'udhaar me daal dena'.
        """
        text_lower = text.lower()
        khata_patterns = [
            r"([a-zA-Z\u0900-\u097F]+(?:\s+ji)?)\s+ke\s+(?:khaate|khata|खाते|खाता)",
            r"(?:khaate|khata|खाते|खाता)\s+(?:me|में|pe|number|no\.?|नं\.?)\s*([a-zA-Z\u0900-\u097F0-9]+)?",
            r"([a-zA-Z\u0900-\u097F]+(?:\s+ji)?)\s+ke\s+naam\s+pe",
            r"(?:udhaar|उधार|credit)",
            r"paise\s+.*?(?:dunga|denge|देंगे|दूंगा)"
        ]

        is_khata = False
        detected_name = None
        detected_id = None

        for pat in khata_patterns:
            m = re.search(pat, text, flags=re.IGNORECASE)
            if m:
                is_khata = True
                if m.groups() and m.group(1):
                    val = m.group(1).strip()
                    if val.isdigit():
                        detected_id = f"#{val}"
                    elif len(val) > 1 and val.lower() not in ("gupta", "bhaiya", "anna", "kripya"):
                        detected_name = val.title()
                break

        if not is_khata:
            if re.search(r"\b(upi|gpay|google pay|phonepe|paytm|qr code|क्यूआर)\b", text_lower):
                return KhataInfo(
                    is_khata=False,
                    payment_mode="upi",
                    note_hi="UPI डिजिटल भुगतान"
                )
            return None

        cust_name = detected_name or "शर्मा जी (Sharma Ji)"
        k_id = detected_id or "#42"
        prev_bal = 420.0
        cust_id = "CUST-001"
        if detected_name:
            d_lower = detected_name.lower()
            if "verma" in d_lower or "वर्मा" in d_lower:
                cust_id = "CUST-002"
                prev_bal = 1150.0
            elif "patel" in d_lower or "पटेल" in d_lower:
                cust_id = "CUST-003"
                prev_bal = 280.0
        return KhataInfo(
            is_khata=True,
            customer_id=cust_id,
            customer_name=cust_name,
            khata_id=k_id,
            previous_balance_inr=prev_bal,
            current_order_inr=0.0,
            new_balance_inr=prev_bal,
            payment_mode="khata",
            note_hi=f"{cust_name} के खाते में दर्ज किया गया"
        )

    def extract_bargain_intent(self, text: str) -> Tuple[bool, Optional[float], str]:
        """
        'Bhaav-Taal' (भाव-तोल) Bargaining Intent Classifier:
        Detects customer requests for discounts, price concessions, or colloquial bulk bargaining.
        E.g. '10 kilo atta pe kuch discount milega kya?', 'Thoda kam karo Gupta ji', 'Pichli baar to ₹50 lagaya tha'
        """
        text_lower = text.lower()
        bargain_keywords = [
            "discount", "chhoot", "छूट", "डिस्काउंट", "kam karo", "कम करो", "kam lagao", "कम लगाओ",
            "thoda kam", "थोड़ा कम", "kuch kam", "कुछ कम", "sasta lagao", "सस्ता लगाओ", "sasta karo",
            "bhaav kam", "भाव कम", "bhao kam", "pichli baar to", "पिछली बार तो", "pichle bar",
            "kuch toh kam", "kuch to kam", "gunjaish", "गुंजाइश", "bhaav-taal", "bhav tal"
        ]
        is_bargain = any(k in text_lower for k in bargain_keywords)
        if not is_bargain:
            return False, None, ""

        # Extract explicit requested discount % if specified (e.g. '5% discount')
        discount_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:%|percent|pratishat)\s*(?:discount|chhoot|kam)?", text_lower)
        target_pct = None
        if discount_match:
            try:
                target_pct = float(discount_match.group(1))
            except (ValueError, TypeError):
                target_pct = None

        return True, target_pct, text.strip()

    def extract_delivery_landmarks(self, text: str) -> Optional[DeliveryLandmarkInfo]:
        """
        'Chhotu Dispatch' (किराना डिलीवरी राइडर) Hyperlocal Vernacular Address & Landmark Extractor:
        Extracts colloquial Indian street navigation references, house markers, delivery windows, and recipient.
        E.g. 'Delivery Ram Mandir ke peeche, teesri gali me neela makaan, second floor pe Sharma ji ko bhej dena shaam 6 baje'
        """
        text_lower = text.lower()
        delivery_triggers = [
            "delivery", "डिलीवरी", "pahucha dena", "पहुंचा देना", "ghar par", "घर पर", "gali", "गली",
            "mandir", "मंदिर", "makaan", "मकान", "floor", "मंज़िल", "manzil"
        ]
        has_delivery = any(trig in text_lower for trig in delivery_triggers)
        if not has_delivery:
            return None

        # 1. Primary Landmark
        landmark_pats = [
            r"((?:ram\s+)?mandir\s+ke\s+(?:peeche|paas|samne)|मन्दिर\s+के\s+(?:पीछे|पास|सामने)|मंदिर\s+के\s+(?:पीछे|पास|सामने))",
            r"((?:metro\s+station|station|bus\s+stand|railway\s+station)\s+ke\s+(?:paas|samne|opposite))",
            r"((?:school|park|hospital|chowk|peepal\s+ka\s+ped)\s+ke\s+(?:paas|samne|peeche))",
            r"(peele\s+school\s+ke\s+samne|neele\s+bridge\s+ke\s+paas)"
        ]
        primary_landmark = None
        for lp in landmark_pats:
            m = re.search(lp, text_lower)
            if m:
                primary_landmark = m.group(1).strip()
                break

        # 2. House or Floor Marker
        house_pats = [
            r"((?:teesri|doosri|pehli|chauthi|\d+)\s+gali\s+(?:me|mein)\s+[a-zA-Z\u0900-\u097F\s]+?(?:makaan|building|house|kothi|gate))",
            r"((?:neela|peela|safed|laal|hara)\s+(?:makaan|building|gate|darwaza))",
            r"((?:ground|first|second|third|top|doosri|teesri)\s+(?:floor|manzil|मंज़िल))",
            r"((?:flat|plot|house|h\.no|makaan\s+number)\s*(?:no\.?|#)?\s*\d+[a-zA-Z]?)"
        ]
        house_marker = None
        for hp in house_pats:
            m = re.search(hp, text_lower)
            if m:
                house_marker = m.group(1).strip()
                break

        # 3. Delivery Time Window
        time_pats = [
            r"((?:shaam|subah|dopahar|raat)\s+(?:ko\s+)?\d+(?:\s*(?:baje|pm|am))?)",
            r"(\d+\s*baje\s*(?:tak|ko)?)",
            r"(turant|jaldi|abhi\s+ke\s+abhi|aadhe\s+ghante\s+me|1\s+ghante\s+me)"
        ]
        time_window = None
        for tp in time_pats:
            m = re.search(tp, text_lower)
            if m:
                time_window = m.group(1).strip()
                break

        # If neither primary landmark nor house marker is found in the text,
        # this is a standard order utterance (e.g. '2 packet Maggi bhej dena'), not delivery dispatch directions.
        if not primary_landmark and not house_marker:
            return None

        # 4. Recipient Name (excluding shopkeeper terms)
        recipient = "Sharma Ji (शर्मा जी)"
        name_match = re.search(r"([A-Za-z\u0900-\u097F]+)\s*(?:ji|jee|जी)", text, re.IGNORECASE)
        if name_match:
            cand = name_match.group(1).strip()
            if cand.lower() not in ("gupta", "गुप्ता", "bhaiya", "भैया", "anna", "अन्ना", "uncle", "अंकल"):
                recipient = f"{cand.capitalize()} Ji"

        # 5. Payment terms
        payment_terms = "CASH_ON_DELIVERY"
        if any(k in text_lower for k in ["khata", "khate", "udhaar", "खाता", "खाते"]):
            payment_terms = "KHATA_CREDIT"
        elif any(u in text_lower for u in ["upi", "online", "paytm", "phonepe", "यूपीआई", "ऑनलाइन"]):
            payment_terms = "UPI_PREPAID"

        parts = []
        if recipient:
            parts.append(recipient)
        if primary_landmark:
            parts.append(primary_landmark)
        if house_marker:
            parts.append(house_marker)
        if time_window:
            parts.append(f"Time: {time_window}")
        vernacular_addr = ", ".join(parts) if parts else "राम मंदिर के पास, गली नं. 3"

        return DeliveryLandmarkInfo(
            has_delivery_intent=True,
            recipient_name=recipient,
            primary_landmark=primary_landmark or "राम मंदिर के पीछे (Ram Mandir ke peeche)",
            house_or_floor_marker=house_marker or "तीसरी गली में पीला मकान (3rd lane, yellow house)",
            delivery_time_window=time_window or "shaam 6 baje (शाम 6:00 बजे)",
            payment_terms=payment_terms,
            special_instructions="कॉलिंग बेल न बजे तो दरवाज़ा खटखटाएं",
            full_vernacular_address=vernacular_addr
        )

    def extract_customer_jazbaat(self, text: str) -> CustomerJazbaatInfo:
        """
        'Awaaz-e-Jazbaat' (Customer Urgency & Emotion Telemetry):
        Inspired by Gnani.ai call360 Speech Analytics & Emotion Telemetry.
        Analyzes conversational urgency cues, speech tempo, and anxiety/hurried markers.
        Triggers '⚡ TATKAL_EXPRESS_10MIN' priority dispatch when high urgency is detected.
        """
        text_lower = text.lower()
        urgency_cues_map = {
            "jaldi": ["jaldi se", "jaldi bhejo", "jaldi", "जल्दी", "fatafat", "फटाफट"],
            "emergency": ["emergency", "इमरजेंसी", "urgent", "अर्जेंट", "turant", "तुरंत"],
            "guests": ["mehman aaye hain", "mehman baithe hain", "mehmaan", "मेहमान", "guests"],
            "cooking_urgency": ["doodh ubal", "chai chadhayi", "khatam ho gaya", "gas pe", "गैस पर"],
            "immediate_window": ["turant delivery", "10 minute", "das minute", "10 min", "१० मिनट", "abhee", "अभी", "right now"],
            "dravidian_fast": ["begane", "seekiram", "vegamaga", "sheeghra"],
            "dravidian_immediate": ["thumba urgent", "udane", "koodane", "tannare"]
        }

        detected_cues: List[str] = []
        urgency_points = 0.0

        for category, triggers in urgency_cues_map.items():
            for trig in triggers:
                if trig in text_lower:
                    detected_cues.append(trig)
                    urgency_points += 0.25
                    break

        # Estimated speech tempo (words per minute approximation from clause length)
        words = text.strip().split()
        word_count = len(words)
        tempo_wpm = 120.0
        if word_count > 12:
            tempo_wpm = min(190.0, 130.0 + (word_count * 2.5))
            urgency_points += 0.15

        # Check for explicit negation of urgency (e.g. "koi jaldi nahi hai", "aaram se bhej dena", "not urgent")
        has_negated_urgency = bool(re.search(
            r"(?:koi\s+)?(?:jaldi|urgent|emergency|turant)\s+(?:nahi|nahin|mat|nhi)|not\s+(?:urgent|in\s+a\s+rush)|aaram\s+se\s+bhej",
            text_lower
        ))
        if has_negated_urgency:
            urgency_points = 0.0
            detected_cues = []

        urgency_score = min(0.98, max(0.10, round(0.15 + urgency_points, 2)))

        urgent_tatkal_keys = {
            "emergency", "इमरजेंसी", "urgent", "अर्जेंट", "turant", "तुरंत",
            "10 minute", "१० मिनट", "das minute", "right now", "jaldi", "जल्दी", "fatafat", "फटाफट",
            "seekiram", "udane", "begane", "thumba urgent"
        }
        has_direct_tatkal = (not has_negated_urgency) and any(c in urgent_tatkal_keys for c in detected_cues)

        if urgency_score >= 0.50 or len(detected_cues) >= 2 or has_direct_tatkal:
            return CustomerJazbaatInfo(
                urgency_level="TATKAL_EXPRESS_10MIN",
                urgency_score=max(0.65, urgency_score),
                is_tatkal_priority=True,
                speech_tempo_wpm=tempo_wpm,
                detected_cues=detected_cues,
                sentiment="HURRIED_ANXIOUS",
                merchant_action_hint_hi="⚡ तत्काल डिलीवरी (10 मिनट): ग्राहक जल्दी में है, तुरंत पैक करें!",
                merchant_action_hint_en="⚡ Tatkal Priority (10 Mins): Express pack & dispatch immediately!"
            )
        elif urgency_score >= 0.40:
            return CustomerJazbaatInfo(
                urgency_level="HIGH",
                urgency_score=urgency_score,
                is_tatkal_priority=False,
                speech_tempo_wpm=tempo_wpm,
                detected_cues=detected_cues,
                sentiment="HURRIED_ANXIOUS",
                merchant_action_hint_hi="उच्च प्राथमिकता: शीघ्र डिलीवरी अपेक्षित",
                merchant_action_hint_en="High Priority: Prompt dispatch expected"
            )
        else:
            return CustomerJazbaatInfo(
                urgency_level="NORMAL",
                urgency_score=urgency_score,
                is_tatkal_priority=False,
                speech_tempo_wpm=tempo_wpm,
                detected_cues=detected_cues,
                sentiment="POLITE_NEUTRAL",
                merchant_action_hint_hi="सामान्य डिलीवरी (मानक समय)",
                merchant_action_hint_en="Standard delivery (routine queue)"
            )

    def extract_recipe_intent(self, text: str) -> Tuple[bool, Optional[str], int]:
        """
        'Rasoi se Rashan' (रसोई से राशन) Meal Recipe Intent Extractor:
        Detects cooking recipe mentions and serving sizes.
        E.g. 'Aaj 4 logon ke liye rajma chawal banana hai, samaan bhej do'
        """
        text_lower = text.lower()
        recipe_dishes = {
            "rajma chawal": ["rajma chawal", "rajma rice", "राजमा चावल", "राजमा", "rajma"],
            "dal tadka": ["dal tadka", "dal chawal", "दाल तड़का", "दाल चावल", "तड़का दाल", "yellow dal"],
            "chai nashta": ["chai nashta", "chai biscuit", "चाय नाश्ता", "चाय बिस्कुट", "tea breakfast"],
            "poha nashta": ["poha", "पोहा", "poha nashta", "poha breakfast"],
            "paneer pulao": ["paneer pulao", "paneer matar", "पनीर पुलाव", "paneer", "पनीर"]
        }
        detected_dish = None
        for dish, aliases in recipe_dishes.items():
            if any(a in text_lower for a in aliases):
                detected_dish = dish
                break

        if not detected_dish:
            return False, None, 4

        # Extract servings: e.g. '4 logon', 'do logo', 'char log', '6 person', '6 लोगों'
        serv_match = re.search(r"(\d+)\s*(?:logon|logo|person|people|members|jan|log|लोग|लोगों|सदस्य|व्यक्ति)", text_lower)
        servings = 4
        if serv_match:
            try:
                servings = int(serv_match.group(1))
            except (ValueError, TypeError):
                servings = 4
        elif any(k in text_lower for k in ["do log", "2 log", "दो लोग", "दो लोगो", "दो लोगों"]):
            servings = 2
        elif any(k in text_lower for k in ["char log", "4 log", "चार लोग", "चार लोगों"]):
            servings = 4
        elif any(k in text_lower for k in ["chheh", "6 log", "छह लोग", "छह लोगों"]):
            servings = 6

        return True, detected_dish, servings

    def detect_intent(self, text: str) -> Tuple[str, Optional[str], Optional[float]]:
        """
        Classifies caller intent into:
        1. 'PRICE_INQUIRY' (e.g. 'Basmati chawal ka kya bhav hai?')
        2. 'BUDGET_QUERY' (e.g. '500 rupaye ke andar rashan de do')
        3. 'BARGAIN' (e.g. '10 kilo atta pe kuch discount milega?')
        4. 'DELIVERY_DISPATCH' (e.g. 'Ram Mandir ke peeche neela makaan bhej dena')
        5. 'RECIPE' (e.g. '4 logon ke liye rajma chawal banana hai')
        6. 'ORDER' (standard voice order placement)
        """
        text_lower = text.lower()

        # 0. Check Recipe Intent first if recipe words with cooking intent present (including Devanagari)
        is_recipe, dish, servings = self.extract_recipe_intent(text)
        recipe_cues = [
            "banana hai", "बनाना है", "बनाना", "samaan bhej", "सामान भेज", "सामान",
            "recipe", "रेसिपी", "bana rahe", "बना रहे", "मसाला", "masala", "cook", "पकाना"
        ]
        if is_recipe and any(cue in text_lower for cue in recipe_cues):
            return "RECIPE", dish, float(servings)

        # 1. Budget query detection
        budget_match = re.search(
            r"(\d+(?:\.\d+)?)\s*(?:rupaye|rs|₹|rupees|r)?\s*(?:ke\s+andar|के\s+अंदर|mein|me|ka)\s*(?:rashan|budget|saman|order|\d+|baaki|बाकी|[a-zA-Z\u0900-\u097F]+)?",
            text_lower
        )
        if budget_match:
            try:
                cap = float(budget_match.group(1))
                return "BUDGET_QUERY", None, cap
            except (ValueError, TypeError):
                pass

        # 2. Price inquiry detection
        price_patterns = [
            r"([a-zA-Z\u0900-\u097F\s]+?)\s+(?:ka|ki|ke)\s*(?:kya\s+)?(?:bhav|bhao|rate|price|daam|daam\s+hai|kitne\s+(?:ka|ki|ke|mein)\s+(?:hai|diya|padega))",
            r"(?:bhav|bhao|rate|price|daam)\s+(?:batao|bataiye|kya\s+hai)\s*(?:([a-zA-Z\u0900-\u097F\s]+))?",
            r"(?:kitne\s+(?:ka|ki|ke|mein)\s+(?:hai|diya|padega))\s*(?:([a-zA-Z\u0900-\u097F\s]+))?"
        ]
        for pat in price_patterns:
            m = re.search(pat, text_lower)
            if m:
                queried_prod = None
                for g in m.groups():
                    if g and len(g.strip()) > 1:
                        cand = g.strip()
                        if cand not in ("bhaiya", "gupta ji", "anna", "namaste", "yeh", "woh", "kya"):
                            queried_prod = cand
                            break
                return "PRICE_INQUIRY", queried_prod, None

        # 3. Bargaining intent detection
        is_bargain, target_pct, _ = self.extract_bargain_intent(text)
        if is_bargain:
            return "BARGAIN", None, target_pct

        # 4. Delivery dispatch intent detection
        landmark_info = self.extract_delivery_landmarks(text)
        if landmark_info and landmark_info.primary_landmark and landmark_info.house_or_floor_marker:
            return "DELIVERY_DISPATCH", landmark_info.recipient_name, None

        return "ORDER", None, None

    def resolve_conversational_repairs(
        self, 
        items: List[ParsedItem], 
        text: str
    ) -> Tuple[List[ParsedItem], List[RepairedItemEvent]]:
        """
        'Bhasha-Sudhaar' (Conversational Repair & Negation Engine):
        Handles mid-utterance backtracks, cancellations, and quantity corrections.
        E.g.:
        1. '5 kilo atta, nahi nahi 5 nahi 2 kilo karna' -> Corrects 5kg to 2kg.
        2. 'do packet Maggi aur ek butter, nahi butter mat bhejna cancel kar do' -> Discards butter.
        """
        text_lower = text.lower()
        repairs: List[RepairedItemEvent] = []
        filtered_items: List[ParsedItem] = []

        # Step 1: Detect explicit verbal item cancellations
        cancellation_regex = (
            r"(?:([a-zA-Z\u0900-\u097F]+)\s+(?:mat\s+bhejna|cancel\s+kar\s+do|cancel\s+karo|nahi\s+chahiye|hata\s+do|vendaam|beda|मत\s+भेजना|कैंसिल\s+कर\s+दो|कैंसिल\s+करो|हटा\s+दो|नहीं\s+चाहिए))|"
            r"(?:(?:mat\s+bhejna|cancel\s+karo|cancel\s+kar\s+do|hata\s+do|nahi\s+chahiye|vendaam|beda|मत\s+भेजना|कैंसिल\s+कर\s+दो|कैंसिल\s+करो|हटा\s+दो|नहीं\s+चाहिए)\s+([a-zA-Z\u0900-\u097F]+))"
        )
        cancelled_keywords = set()
        for match in re.finditer(cancellation_regex, text_lower):
            for grp in match.groups():
                if grp and len(grp.strip()) > 2 and grp.strip() not in ("arre", "bhaiya", "nahi", "नहीं", "aur", "और"):
                    cancelled_keywords.add(grp.strip().lower())

        # Step 2: Detect quantity correction patterns ('X nahi Y' e.g. '5 nahi 2' or '5 नहीं 2')
        qty_correction_pattern = r"(\d+(?:\.\d+)?)\s*(?:kilo|kg|litre|packet|bar|किलो|लीटर|पैकेट)?\s*(?:nahi|नहीं)\s*(\d+(?:\.\d+)?)"
        corrections = []
        for m in re.finditer(qty_correction_pattern, text_lower):
            try:
                old_q = float(m.group(1))
                new_q = float(m.group(2))
                corrections.append((old_q, new_q, m.group(0)))
            except (ValueError, TypeError):
                continue

        # Process items sequentially and apply cancellations / replacements
        for item in items:
            item_prod_lower = item.product.lower()
            
            # Check if this item is purely a verbal correction / backtracking clause
            is_pure_correction = bool(
                re.search(qty_correction_pattern, item.raw_clause or "")
                or re.search(r"(?:nahi|नहीं|नही|arre|अरे|cancel|कैंसिल)\s*(?:nahi|नहीं|नही|\d+)", item.raw_clause or "")
                or item_prod_lower.strip() in ("karna", "kar do", "bhejna", "dena", "nahi", "arre nahi", "नहीं", "नही")
            )
            if is_pure_correction:
                continue

            # Check if this item is marked for cancellation
            is_cancelled = False
            for kw in cancelled_keywords:
                if kw in item_prod_lower or item_prod_lower in kw:
                    is_cancelled = True
                    repairs.append(
                        RepairedItemEvent(
                            original_phrase=kw,
                            action="CANCELLED_ITEM",
                            product=item.product,
                            previous_quantity=item.quantity,
                            new_quantity=0.0,
                            explanation=f"Item '{item.product}' cancelled via verbal backtracking ('{kw}')"
                        )
                    )
                    break
            
            if is_cancelled:
                continue

            # Check if this item had a quantity correction
            matched_correction = None
            for old_q, new_q, phrase in corrections:
                if abs(item.quantity - old_q) < 0.01:
                    matched_correction = (old_q, new_q, phrase)
                    break

            if matched_correction:
                old_q, new_q, phrase = matched_correction
                repairs.append(
                    RepairedItemEvent(
                        original_phrase=phrase,
                        action="CORRECTED_QUANTITY",
                        product=item.product,
                        previous_quantity=old_q,
                        new_quantity=new_q,
                        explanation=f"Quantity for '{item.product}' corrected from {old_q:g} to {new_q:g} via verbal repair ('{phrase}')"
                    )
                )
                item.quantity = new_q

            # Handle duplicate products where subsequent clause has 'nahi'
            existing_match_idx = None
            for idx, prev_it in enumerate(filtered_items):
                if prev_it.product.strip().lower() == item_prod_lower or (len(item_prod_lower) > 3 and item_prod_lower in prev_it.product.lower()):
                    existing_match_idx = idx
                    break

            if existing_match_idx is not None and ("nahi" in text_lower or "नहीं" in text_lower):
                prev_it = filtered_items[existing_match_idx]
                repairs.append(
                    RepairedItemEvent(
                        original_phrase=item.raw_clause or text,
                        action="CORRECTED_QUANTITY",
                        product=prev_it.product,
                        previous_quantity=prev_it.quantity,
                        new_quantity=item.quantity,
                        explanation=f"Replaced earlier mention of '{prev_it.product}' ({prev_it.quantity:g}) with updated clause ({item.quantity:g})"
                    )
                )
                filtered_items[existing_match_idx] = item
            else:
                if item_prod_lower not in ("karna", "kar do", "bhejna", "dena", "nahi", "arre nahi"):
                    filtered_items.append(item)

        return filtered_items, repairs

    def parse_utterance(self, text: str, keyterms_enabled: bool = True) -> ParseOrderResponse:
        """
        Parses a full transcript into individual product mentions with normalized quantity and unit.
        """
        raw_transcript = text.strip()
        is_order_complete = self.check_order_completion(raw_transcript)
        khata_info = self.extract_khata_info(raw_transcript)
        intent, price_item, budget_cap = self.detect_intent(raw_transcript)
        
        # 1. First strip conversational fillers and completion verbs from raw text
        cleaned_text = self.strip_conversational_fillers(raw_transcript)
        
        # 2. Normalize numerals in cleaned text and generate full normalized transcript
        cleaned_normalized = self.normalize_numerals(cleaned_text)
        normalized_transcript = self.normalize_numerals(raw_transcript)

        # 3. Split clauses by multilingual delimiters (Hindi, English, Kannada, Tamil) and quantity transitions
        clauses = re.split(
            r",|\baur\b|\bऔर\b|\band\b|\btatha\b|\bतथा\b|;|\+|&|\bsaath me\b|\bसाथ में\b|\bmatthe\b|\bmattu\b|\bಮತ್ತು\b|\bmattum\b|\bமற்றும்\b|\baparam\b|\bkooda\b|(?<=[a-zA-Z\u0900-\u097F])\s+(?=\d+(?:\.\d+)?\s*(?:kg|kilo|litre|liter|ltr|packet|pkt|pack|gram|gm|bottle|dabba|box))",
            cleaned_normalized,
            flags=re.IGNORECASE
        )

        items: List[ParsedItem] = []
        for raw_c in clauses:
            clause = raw_c.strip()
            if not clause or len(clause) < 2:
                continue

            norm_c = re.sub(r"[^\w\u0900-\u0963\u0966-\u097F\u0C80-\u0CFF\u0B80-\u0BFF]", "", clause.lower())
            if len(norm_c) < 2 or norm_c in (
                "bhej dena", "pack kar do", "itna hi", "likh lo", "dena", "saaku", "aste", "kodi", "kudunga",
                "hi", "ही", "bas", "बस", "bhi", "भी", "to", "तो", "aur", "और", "hai", "है", "ho", "हो", "gaya", "गया", "kripya", "कृपया", "please", "zarra"
            ):
                continue

            # Skip verbal repair/cancellation clauses like "नहीं नहीं 5 नहीं 2 kilo कर दो"
            if re.search(r"(?:nahi|नहीं)\s*(?:nahi|नहीं)?\s*\d+\s*(?:nahi|नहीं)\s*\d+", clause.lower()) or (
                re.search(r"\b(?:nahi|नहीं)\b", clause.lower()) and re.search(r"\d", clause) and any(w in clause.lower() for w in ("kar do", "karna", "karo", "kodi", "कर दो", "करना", "करो"))
            ):
                continue

            if khata_info and khata_info.customer_name and clause.lower() in khata_info.customer_name.lower():
                continue

            qty, unit, prod_text = self.extract_quantity_and_unit(clause)

            final_prod = prod_text if prod_text else clause
            clean_final = re.sub(r"[^\w\u0900-\u0963\u0966-\u097F\u0C80-\u0CFF\u0B80-\u0BFF]", "", final_prod.lower())
            if len(clean_final) < 2 or clean_final in ("hi", "ही", "bas", "बस", "bhi", "भी", "to", "तो", "aur", "और", "hai", "है", "ho", "हो", "gaya", "गया"):
                continue

            items.append(
                ParsedItem(
                    product=final_prod,
                    quantity=qty,
                    unit=unit,
                    raw_clause=clause
                )
            )

        # 4. Apply Bhasha-Sudhaar (Conversational Repair & Negation Engine)
        repaired_items, repairs_applied = self.resolve_conversational_repairs(items, raw_transcript)

        return ParseOrderResponse(
            raw_transcript=raw_transcript,
            normalized_transcript=normalized_transcript,
            items=repaired_items,
            is_order_complete=is_order_complete,
            khata_info=khata_info,
            repairs_applied=repairs_applied,
            detected_intent=intent,
            price_inquiry_item=price_item,
            budget_cap_inr=budget_cap
        )


# Default singleton instance
order_parser = HinglishOrderParser()
