import React, { useState, useEffect } from "react";
import { 
  X, 
  Tag, 
  Percent, 
  ShieldCheck, 
  Volume2, 
  Sparkles, 
  ArrowRight, 
  CheckCircle2, 
  RotateCcw,
  TrendingDown,
  Store
} from "lucide-react";
import { CartItem } from "./ShoppingCart";

interface BhaavTaalDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  apiBaseUrl: string;
  cartItems: CartItem[];
  customerName?: string;
  onApplyDiscountedTotal?: (discountedTotal: number, discountAmount: number) => void;
}

export const BhaavTaalDrawer: React.FC<BhaavTaalDrawerProps> = ({
  isOpen,
  onClose,
  apiBaseUrl,
  cartItems,
  customerName = "Sharma Ji (शर्मा जी)",
  onApplyDiscountedTotal
}) => {
  const [targetDiscountPct, setTargetDiscountPct] = useState<number>(6.0);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [bhaavResult, setBhaavResult] = useState<any | null>(null);

  useEffect(() => {
    if (isOpen) {
      handleNegotiate();
    }
  }, [isOpen]);

  const handleNegotiate = async (overrideDiscount?: number) => {
    setIsLoading(true);
    try {
      const itemsPayload = cartItems.map((it) => ({
        sku_id: it.sku_id,
        quantity: it.quantity,
        unit: it.unit
      }));

      const res = await fetch(`${apiBaseUrl}/negotiate-bhav`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer_name: customerName,
          cart_items: itemsPayload,
          target_discount_pct: overrideDiscount ?? targetDiscountPct
        })
      });

      if (res.ok) {
        const data = await res.json();
        setBhaavResult(data);
      }
    } catch (e) {
      console.warn("Bhaav-Taal negotiation error:", e);
    } finally {
      setIsLoading(false);
    }
  };

  const playVoiceCounterOffer = () => {
    if (bhaavResult?.voice_audio_base64) {
      const audio = new Audio(`data:audio/${bhaavResult.voice_audio_format || "wav"};base64,${bhaavResult.voice_audio_base64}`);
      audio.play().catch((e) => console.warn("Voice play error:", e));
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
      <div className="w-full max-w-2xl bg-slate-900 border border-amber-500/40 rounded-2xl shadow-2xl shadow-amber-500/10 overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-4 bg-gradient-to-r from-amber-950/60 to-slate-900 border-b border-amber-500/30 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-300">
              <Tag className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white tracking-tight">
                  Bhaav-Taal (भाव-तोल) • Kirana Voice Bargaining Engine
                </h3>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 font-bold border border-amber-500/30">
                  APMC MARGIN
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Dynamic wholesale spread calculation & conversational margin negotiation via Gnani Timbre
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 space-y-4 overflow-y-auto">
          {/* Customer Loyalty Banner */}
          <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span className="text-slate-300">
                Customer: <strong className="text-white">{customerName}</strong>
              </span>
            </div>
            <span className="text-[10px] font-mono font-bold px-2.5 py-1 rounded-md bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              {bhaavResult?.loyalty_tier || "PLATINUM LOYALTY (पुराना खाता)"}
            </span>
          </div>

          {/* Metric Comparison Cards */}
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-center">
              <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-0.5">Original Retail Bill</div>
              <div className="text-lg font-bold text-slate-300 line-through">
                ₹{bhaavResult?.original_total_inr?.toFixed(2) || "465.00"}
              </div>
            </div>

            <div className="p-3 rounded-xl bg-gradient-to-br from-amber-950/40 to-slate-950 border border-amber-500/40 text-center">
              <div className="text-[10px] text-amber-300 uppercase tracking-wider mb-0.5 font-bold">Negotiated Total</div>
              <div className="text-xl font-bold text-amber-400">
                ₹{bhaavResult?.negotiated_total_inr?.toFixed(2) || "430.00"}
              </div>
            </div>

            <div className="p-3 rounded-xl bg-emerald-950/30 border border-emerald-500/30 text-center">
              <div className="text-[10px] text-emerald-300 uppercase tracking-wider mb-0.5 font-bold">Customer Savings</div>
              <div className="text-lg font-bold text-emerald-400 flex items-center justify-center gap-1">
                <TrendingDown className="w-4 h-4" />
                <span>₹{bhaavResult?.total_savings_inr?.toFixed(2) || "35.00"}</span>
              </div>
            </div>
          </div>

          {/* Quick Target Discount Sliders / Buttons */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span>Target Discount Rate:</span>
              <span className="font-mono font-bold text-amber-300">{targetDiscountPct}%</span>
            </div>
            <div className="flex gap-2">
              {[4, 5, 6, 7.5, 9].map((pct) => (
                <button
                  key={pct}
                  onClick={() => {
                    setTargetDiscountPct(pct);
                    handleNegotiate(pct);
                  }}
                  className={`flex-1 py-1.5 text-xs font-mono font-bold rounded-lg border transition-all ${
                    targetDiscountPct === pct
                      ? "bg-amber-500/20 text-amber-300 border-amber-500/40 shadow-sm shadow-amber-500/20"
                      : "bg-slate-800 text-slate-400 border-slate-700 hover:text-white"
                  }`}
                >
                  {pct}%
                </button>
              ))}
            </div>
          </div>

          {/* Spoken Counter-Offer Dialogue */}
          {bhaavResult?.spoken_counter_offer_hi && (
            <div className="p-4 rounded-xl bg-gradient-to-r from-amber-950/40 to-slate-950 border border-amber-500/30 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-amber-300 uppercase tracking-wide flex items-center gap-1.5">
                  <Store className="w-3.5 h-3.5" />
                  दुकानदार का उत्तर (Timbre TTS Spoken Banter):
                </span>
                {bhaavResult.voice_audio_base64 && (
                  <button
                    onClick={playVoiceCounterOffer}
                    className="p-1 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/30 transition-colors flex items-center gap-1 text-[11px] px-2"
                  >
                    <Volume2 className="w-3.5 h-3.5" />
                    <span>Play Voice</span>
                  </button>
                )}
              </div>
              <p className="text-xs text-slate-200 font-hindi italic leading-relaxed">
                "{bhaavResult.spoken_counter_offer_hi}"
              </p>
              <div className="text-[10px] text-slate-400 font-mono">
                Merchant Gross Margin Preserved: <strong>{bhaavResult.merchant_margin_preserved_pct}%</strong> (APMC Viability Safe)
              </div>
            </div>
          )}

          {/* Itemized Margin Table */}
          {bhaavResult?.bargain_items && bhaavResult.bargain_items.length > 0 && (
            <div className="space-y-1.5">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                Wholesale Margin Breakdown per SKU:
              </span>
              <div className="border border-slate-800 rounded-xl overflow-hidden text-xs">
                <table className="w-full text-left">
                  <thead className="bg-slate-950/80 text-slate-400 text-[10px] font-mono border-b border-slate-800">
                    <tr>
                      <th className="py-2 px-3">Item</th>
                      <th className="py-2 px-2 text-right">Retail MRP</th>
                      <th className="py-2 px-2 text-right">Mandi Cost</th>
                      <th className="py-2 px-2 text-right text-amber-300">Negotiated Rate</th>
                      <th className="py-2 px-3 text-right text-emerald-400">Margin</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {bhaavResult.bargain_items.map((it: any) => (
                      <tr key={it.sku_id} className="hover:bg-slate-800/40">
                        <td className="py-2 px-3">
                          <div className="font-medium text-white">{it.name_en}</div>
                          <div className="text-[10px] text-slate-400 font-hindi">{it.name_hi}</div>
                        </td>
                        <td className="py-2 px-2 text-right text-slate-300">₹{it.retail_rate_inr}</td>
                        <td className="py-2 px-2 text-right text-slate-500 font-mono">₹{it.wholesale_cost_inr}</td>
                        <td className="py-2 px-2 text-right text-amber-300 font-bold">₹{it.offered_rate_inr}</td>
                        <td className="py-2 px-3 text-right text-emerald-400 font-mono font-bold">
                          +₹{it.margin_preserved_inr}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-4 bg-slate-950 border-t border-slate-800 flex items-center justify-between gap-3">
          <button
            onClick={() => handleNegotiate()}
            disabled={isLoading}
            className="px-3 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors flex items-center gap-1.5"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
            <span>Recalculate Margin</span>
          </button>

          <button
            onClick={() => {
              if (bhaavResult && onApplyDiscountedTotal) {
                onApplyDiscountedTotal(bhaavResult.negotiated_total_inr, bhaavResult.total_savings_inr);
              }
              onClose();
            }}
            className="px-5 py-2 rounded-xl text-xs font-bold bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 flex items-center gap-1.5 shadow-lg shadow-amber-500/20 transition-all"
          >
            <CheckCircle2 className="w-4 h-4" />
            <span>Accept ₹{bhaavResult?.negotiated_total_inr || "430"} Counter-Offer</span>
          </button>
        </div>
      </div>
    </div>
  );
};
