import React from "react";
import { ShoppingCart as CartIcon, Trash2, Tag, Sparkles, Plus, Check } from "lucide-react";

export interface CartItem {
  sku_id: string;
  name_en: string;
  name_hi: string;
  category: string;
  quantity: number;
  unit: string;
  unit_price: number;
  line_total: number;
}

export interface UpsellSuggestion {
  sku_id: string;
  name_en: string;
  name_hi: string;
  category: string;
  price_inr: number;
  unit: string;
  quantity: number;
  pitch_hi: string;
  pitch_en: string;
  reason_tag: string;
}

interface ShoppingCartProps {
  items: CartItem[];
  onRemoveItem: (skuId: string) => void;
  upsellSuggestion?: UpsellSuggestion | null;
  onAddUpsellItem?: (upsell: UpsellSuggestion) => void;
}

export const ShoppingCart: React.FC<ShoppingCartProps> = ({
  items,
  onRemoveItem,
  upsellSuggestion,
  onAddUpsellItem
}) => {
  if (!items || items.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2 mb-2">
          <CartIcon className="w-5 h-5 text-teal-400" />
          Confirmed Cart Items
        </h2>
        <div className="text-center py-12 text-slate-500 text-sm">
          Cart is empty. Speak an order to automatically add items.
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <CartIcon className="w-5 h-5 text-teal-400" />
          Confirmed Cart Items ({items.length})
        </h2>
        <span className="text-xs text-teal-400 font-medium bg-teal-500/10 px-2 py-0.5 rounded-full border border-teal-500/20">
          Matched to Kirana SKU
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-950/80 text-slate-400 font-semibold border-b border-slate-800">
            <tr>
              <th className="py-2.5 px-3">Item & Category</th>
              <th className="py-2.5 px-2 text-center">Qty</th>
              <th className="py-2.5 px-2 text-right">Rate</th>
              <th className="py-2.5 px-3 text-right">Total</th>
              <th className="py-2.5 px-2 text-center"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {items.map((item) => (
              <tr key={item.sku_id} className="hover:bg-slate-800/40 transition-colors">
                <td className="py-2.5 px-3">
                  <div className="font-semibold text-white text-xs">{item.name_en}</div>
                  <div className="text-[11px] text-slate-400 font-hindi">{item.name_hi}</div>
                  <div className="flex items-center gap-1 mt-0.5">
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400">
                      {item.category}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">{item.sku_id}</span>
                  </div>
                </td>

                <td className="py-2.5 px-2 text-center font-mono font-medium text-slate-200">
                  {item.quantity} {item.unit}
                </td>

                <td className="py-2.5 px-2 text-right text-slate-400">
                  ₹{item.unit_price}
                </td>

                <td className="py-2.5 px-3 text-right font-semibold text-teal-300">
                  ₹{item.line_total.toFixed(2)}
                </td>

                <td className="py-2.5 px-2 text-center">
                  <button
                    onClick={() => onRemoveItem(item.sku_id)}
                    className="p-1 rounded text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                    title="Remove item from cart"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Dukandar ki Salah (दुकानदार की सलाह) — Smart Kirana Cross-Sell Banner */}
      {upsellSuggestion && onAddUpsellItem && (
        <div className="p-3.5 rounded-xl bg-gradient-to-r from-teal-950/50 to-emerald-950/50 border border-teal-500/30 flex items-center justify-between gap-3">
          <div className="space-y-0.5">
            <div className="flex items-center gap-1.5 text-xs font-bold text-teal-300">
              <Sparkles className="w-3.5 h-3.5 text-teal-400 animate-spin" />
              दुकानदार की सलाह (Smart Kirana Cross-Sell):
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-teal-500/20 text-teal-200 border border-teal-500/30">
                {upsellSuggestion.reason_tag}
              </span>
            </div>
            <p className="text-xs text-slate-200 font-hindi">
              "{upsellSuggestion.pitch_hi}"
            </p>
            <p className="text-[10px] text-slate-400 italic">
              {upsellSuggestion.pitch_en}
            </p>
          </div>

          <button
            onClick={() => onAddUpsellItem(upsellSuggestion)}
            className="px-3 py-1.5 rounded-lg bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold text-xs flex items-center gap-1 flex-shrink-0 shadow-lg shadow-teal-500/20 transition-all"
          >
            <Plus className="w-3.5 h-3.5" />
            + Add {upsellSuggestion.name_en.split(" ")[0]} (₹{upsellSuggestion.price_inr})
          </button>
        </div>
      )}
    </div>
  );
};

