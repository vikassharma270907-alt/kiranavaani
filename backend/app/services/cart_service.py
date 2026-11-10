"""
Shopping Cart Service.
Constructs structured shopping carts, calculates line totals, subtotals, and delivery charges,
and synthesizes natural Hinglish/Hindi conversational summaries for Timbre TTS readbacks.
"""
from __future__ import annotations
import logging
from typing import List, Dict, Any, Optional, Tuple

from backend.app.schemas import (
    CartItem,
    CartItemInput,
    CartRequest,
    CartResponse,
    CatalogueSKU,
    UpsellSuggestion
)
from backend.app.services.catalogue_matcher import catalogue_matcher

logger = logging.getLogger(__name__)


class CartService:
    def __init__(self):
        pass

    def compute_upsell_suggestion(self, cart_items: List[CartItem]) -> Optional[UpsellSuggestion]:
        """
        Dukandar ki Salah (दुकानदार की सलाह) — Authentic Kirana Smart Upsell & Cross-Sell Engine.
        Analyzes basket affinities and generates authentic Indian merchant suggestions in Timbre TTS.
        """
        sku_set = {item.sku_id for item in cart_items}
        if not sku_set:
            return None

        # 1. Chai/Coffee + Sugar -> Parle-G Biscuit or Good Day
        has_tea_coffee = any(s in sku_set for s in ["SKU-024", "SKU-025", "SKU-026"])
        has_sugar = "SKU-020" in sku_set
        has_biscuit = any(s in sku_set for s in ["SKU-031", "SKU-032"])
        if (has_tea_coffee or has_sugar) and not has_biscuit:
            parle_g = catalogue_matcher.get_sku("SKU-031")
            if parle_g and getattr(parle_g, "in_stock", True):
                return UpsellSuggestion(
                    sku_id=parle_g.sku_id,
                    name_en=parle_g.name_en,
                    name_hi=parle_g.name_hi,
                    category=parle_g.category,
                    price_inr=parle_g.price_inr,
                    unit=parle_g.unit,
                    quantity=1.0,
                    pitch_hi="चाय-चीनी के साथ 1 पैकेट ₹10 वाला पारले-जी बिस्कुट भी डाल दें?",
                    pitch_en="Along with tea and sugar, should I add a pack of ₹10 Parle-G biscuits?",
                    reason_tag="चाय + बिस्कुट (Chai + Biscuit)"
                )

        # 2. Atta / Maida -> Amul Pure Cow Ghee or Mustard Oil
        has_flour = any(s in sku_set for s in ["SKU-001", "SKU-005"])
        has_oil_ghee = any(s in sku_set for s in ["SKU-016", "SKU-017", "SKU-018"])
        if has_flour and not has_oil_ghee:
            ghee = catalogue_matcher.get_sku("SKU-018")
            if ghee and getattr(ghee, "in_stock", True):
                return UpsellSuggestion(
                    sku_id=ghee.sku_id,
                    name_en=ghee.name_en,
                    name_hi=ghee.name_hi,
                    category=ghee.category,
                    price_inr=ghee.price_inr,
                    unit=ghee.unit,
                    quantity=1.0,
                    pitch_hi="गरम रोटियों के लिए शुद्ध अमूल गाय का घी (₹320) भी चाहिए?",
                    pitch_en="Would you like pure Amul Cow Ghee (₹320) for fresh rotis?",
                    reason_tag="आटा + शुद्ध घी (Atta + Shuddh Ghee)"
                )

        # 3. Dal / Pulses or Rice -> Tata Salt or MDH Haldi
        has_dal_rice = any(s in sku_set for s in ["SKU-002", "SKU-003", "SKU-007", "SKU-008", "SKU-009"])
        has_spices = any(s in sku_set for s in ["SKU-019", "SKU-021", "SKU-022", "SKU-023"])
        if has_dal_rice and not has_spices:
            salt = catalogue_matcher.get_sku("SKU-019")
            if salt and getattr(salt, "in_stock", True):
                return UpsellSuggestion(
                    sku_id=salt.sku_id,
                    name_en=salt.name_en,
                    name_hi=salt.name_hi,
                    category=salt.category,
                    price_inr=salt.price_inr,
                    unit=salt.unit,
                    quantity=1.0,
                    pitch_hi="दाल-चावल के साथ क्या 1 किलो टाटा नमक (₹28) भी लिख लें?",
                    pitch_en="Along with dal and rice, shall we add 1 kg Tata Salt (₹28)?",
                    reason_tag="दाल-चावल + नमक (Staple Combo)"
                )

        # 4. Maggi -> Kurkure Masala Munch
        has_maggi = any(s in sku_set for s in ["SKU-027", "SKU-028"])
        has_snacks = any(s in sku_set for s in ["SKU-029", "SKU-030"])
        if has_maggi and not has_snacks:
            kurkure = catalogue_matcher.get_sku("SKU-029")
            if kurkure and getattr(kurkure, "in_stock", True):
                return UpsellSuggestion(
                    sku_id=kurkure.sku_id,
                    name_en=kurkure.name_en,
                    name_hi=kurkure.name_hi,
                    category=kurkure.category,
                    price_inr=kurkure.price_inr,
                    unit=kurkure.unit,
                    quantity=1.0,
                    pitch_hi="मैगी के साथ 1 पैकेट कुरकुरे मसाला मंच (₹20) भी जोड़ दें?",
                    pitch_en="Along with Maggi, shall we add a pack of Kurkure Masala Munch (₹20)?",
                    reason_tag="नाश्ता कॉम्बो (Snack Combo)"
                )

        return None

    def build_cart(
        self,
        items_input: List[CartItemInput],
        khata_info: Optional[Any] = None
    ) -> CartResponse:
        """
        Builds a structured cart from confirmed item inputs with SKU lookups and totals.
        """
        cart_items: List[CartItem] = []
        subtotal = 0.0

        for inp in items_input:
            sku: Optional[CatalogueSKU] = catalogue_matcher.get_sku(inp.sku_id)
            if not sku:
                logger.warning(f"SKU {inp.sku_id} not found in catalogue. Skipping.")
                continue

            raw_qty = inp.quantity
            unit = (inp.unit or sku.unit).lower()

            # Automatic unit normalization to catalogue SKU pricing unit
            normalized_qty = raw_qty
            final_unit = unit

            if sku.unit.lower() == "kg":
                if unit in ("gram", "gm", "g", "grams", "ग्राम"):
                    normalized_qty = round(raw_qty / 1000.0, 3)
                    final_unit = "kg"
                else:
                    final_unit = "kg"
            elif sku.unit.lower() in ("litre", "liter"):
                if unit in ("ml", "मिली"):
                    normalized_qty = round(raw_qty / 1000.0, 3)
                    final_unit = "litre"
                else:
                    final_unit = "litre"

            line_total = round(normalized_qty * sku.price_inr, 2)
            subtotal += line_total

            cart_items.append(
                CartItem(
                    sku_id=sku.sku_id,
                    name_en=sku.name_en,
                    name_hi=sku.name_hi,
                    category=sku.category,
                    quantity=normalized_qty,
                    unit=final_unit,
                    unit_price=sku.price_inr,
                    line_total=line_total
                )
            )

        subtotal = round(subtotal, 2)
        total = subtotal

        # Update Khata totals if applicable
        if khata_info and hasattr(khata_info, "is_khata") and khata_info.is_khata:
            khata_info.current_order_inr = total
            khata_info.new_balance_inr = round(khata_info.previous_balance_inr + total, 2)

        # Calculate Dukandar ki Salah (Smart Cross-Sell Suggestion)
        upsell = self.compute_upsell_suggestion(cart_items)

        # Build natural spoken summaries
        summary_hi, summary_en = self._generate_spoken_summaries(cart_items, total, khata_info, upsell)

        return CartResponse(
            items=cart_items,
            item_count=len(cart_items),
            subtotal_inr=subtotal,
            delivery_fee_inr=0.0,
            total_inr=total,
            spoken_summary_hi=summary_hi,
            spoken_summary_en=summary_en,
            upsell_suggestion=upsell
        )

    def _generate_spoken_summaries(
        self,
        items: List[CartItem],
        total: float,
        khata_info: Optional[Any] = None,
        upsell: Optional[UpsellSuggestion] = None
    ) -> tuple[str, str]:
        if not items:
            return (
                "आपका कार्ट खाली है। कृपया बताएं आपको क्या चाहिए?",
                "Your cart is empty. Please state what groceries you need."
            )

        hi_phrases = []
        en_phrases = []

        for it in items:
            qty_str = f"{it.quantity:g}"
            hi_phrases.append(f"{qty_str} {it.unit} {it.name_hi}")
            en_phrases.append(f"{qty_str} {it.unit} {it.name_en}")

        hi_items_str = ", ".join(hi_phrases)
        en_items_str = ", ".join(en_phrases)

        hi_total_str = f"{int(total)}" if total == int(total) else f"{total:.2f}"
        
        if khata_info and hasattr(khata_info, "is_khata") and khata_info.is_khata:
            hi_summary = (
                f"आपके ऑर्डर में {hi_items_str} शामिल है। यह ₹{hi_total_str} {khata_info.customer_name} के खाते में दर्ज किया गया है। "
                f"कुल बकाया ₹{int(khata_info.new_balance_inr)} हुआ।"
            )
            en_summary = (
                f"Your order of {en_items_str} totaling ₹{total:g} is booked under {khata_info.customer_name}'s ledger. "
                f"New outstanding balance is ₹{khata_info.new_balance_inr:g}."
            )
        else:
            hi_summary = f"आपके ऑर्डर में {hi_items_str} शामिल है। कुल बिल {hi_total_str} रुपये हुआ है। ऑर्डर कन्फर्म करें?"
            en_summary = f"Your order includes {en_items_str}. Total bill is ₹{total:g}. Would you like to confirm?"

        return hi_summary, en_summary


# Default singleton instance
cart_service = CartService()
