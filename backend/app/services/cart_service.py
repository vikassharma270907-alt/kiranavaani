"""
Shopping Cart Service.
Constructs structured shopping carts, calculates line totals, subtotals, and delivery charges,
and synthesizes natural Hinglish/Hindi conversational summaries for Timbre TTS readbacks.
"""
import logging
from typing import List, Dict, Any, Optional

from backend.app.schemas import (
    CartItem,
    CartItemInput,
    CartRequest,
    CartResponse,
    CatalogueSKU
)
from backend.app.services.catalogue_matcher import catalogue_matcher

logger = logging.getLogger(__name__)


class CartService:
    def __init__(self):
        pass

    def build_cart(self, items_input: List[CartItemInput]) -> CartResponse:
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

            qty = inp.quantity
            unit = inp.unit or sku.unit
            line_total = round(qty * sku.price_inr, 2)
            subtotal += line_total

            cart_items.append(
                CartItem(
                    sku_id=sku.sku_id,
                    name_en=sku.name_en,
                    name_hi=sku.name_hi,
                    category=sku.category,
                    quantity=qty,
                    unit=unit,
                    unit_price=sku.price_inr,
                    line_total=line_total
                )
            )

        subtotal = round(subtotal, 2)
        total = subtotal

        # Build natural spoken summaries
        summary_hi, summary_en = self._generate_spoken_summaries(cart_items, total)

        return CartResponse(
            items=cart_items,
            item_count=len(cart_items),
            subtotal_inr=subtotal,
            delivery_fee_inr=0.0,
            total_inr=total,
            spoken_summary_hi=summary_hi,
            spoken_summary_en=summary_en
        )

    def _generate_spoken_summaries(self, items: List[CartItem], total: float) -> tuple[str, str]:
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

        hi_summary = f"आपके ऑर्डर में {hi_items_str} शामिल है। कुल बिल {int(total)} रुपये हुआ है। ऑर्डर कन्फर्म करें?"
        en_summary = f"Your order includes {en_items_str}. Total bill is ₹{total:g}. Would you like to confirm?"

        return hi_summary, en_summary


# Default singleton instance
cart_service = CartService()
