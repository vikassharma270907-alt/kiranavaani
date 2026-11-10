import React, { useState, useEffect } from "react";
import { 
  Boxes, 
  X, 
  AlertTriangle, 
  Send, 
  CheckCircle2, 
  Volume2, 
  Plus, 
  RefreshCw, 
  ExternalLink,
  ShoppingBag,
  TrendingUp,
  Truck
} from "lucide-react";

export interface MandiReorderTrigger {
  sku_id: string;
  name_en: string;
  name_hi: string;
  current_stock: number;
  unit: string;
  reorder_threshold: number;
  suggested_reorder_qty: number;
  wholesale_rate_inr: number;
  total_wholesale_cost_inr: number;
  wholesaler_name: string;
  wholesaler_phone: string;
  spoken_alert_hi: string;
  spoken_alert_en: string;
  whatsapp_po_text: string;
}

interface MandiRestockDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  apiBaseUrl: string;
}

export const MandiRestockDrawer: React.FC<MandiRestockDrawerProps> = ({
  isOpen,
  onClose,
  apiBaseUrl
}) => {
  const [inventoryItems, setInventoryItems] = useState<any[]>([]);
  const [triggers, setTriggers] = useState<MandiReorderTrigger[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [dispatchSuccess, setDispatchSuccess] = useState<string | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const audioRef = React.useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchInventoryStatus();
    }
  }, [isOpen]);

  const fetchInventoryStatus = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${apiBaseUrl}/inventory/status`);
      if (res.ok) {
        const data = await res.json();
        setInventoryItems(data.inventory_items || []);
        setTriggers(data.reorder_triggers || []);
      }
    } catch (e) {
      console.warn("Could not fetch inventory status:", e);
    } finally {
      setIsLoading(false);
    }
  };

  const dispatchMandiOrder = async (trigger: MandiReorderTrigger) => {
    try {
      const res = await fetch(`${apiBaseUrl}/inventory/mandi-order`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sku_id: trigger.sku_id,
          reorder_quantity: trigger.suggested_reorder_qty,
          wholesaler_name: trigger.wholesaler_name,
          wholesaler_phone: trigger.wholesaler_phone
        })
      });
      if (res.ok) {
        const data = await res.json();
        setDispatchSuccess(data.spoken_confirmation_hi);
        if (data.voice_audio_base64) {
          const a = new Audio(`data:audio/${data.voice_audio_format || "wav"};base64,${data.voice_audio_base64}`);
          audioRef.current = a;
          a.play();
        }
        // Open WhatsApp link in new tab
        if (data.whatsapp_url) {
          window.open(data.whatsapp_url, "_blank");
        }
        // Refresh inventory
        fetchInventoryStatus();
      }
    } catch (e) {
      console.error("Mandi order dispatch failed:", e);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/70 backdrop-blur-sm animate-fade-in flex justify-end">
      <div className="w-full max-w-xl bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col h-full overflow-hidden">
        {/* Drawer Header */}
        <div className="p-5 border-b border-slate-800 bg-slate-950 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
              <Boxes className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white">
                  Mandi Wholesale B2B Restock <span className="text-amber-400 font-hindi font-normal text-sm">(थोक मंडी रीऑर्डर)</span>
                </h3>
              </div>
              <p className="text-xs text-slate-400">
                Live Store Inventory & Automated APMC Wholesaler Purchase Orders
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 overflow-y-auto space-y-6 flex-1">
          {/* Dispatch Toast */}
          {dispatchSuccess && (
            <div className="p-3.5 rounded-xl bg-emerald-950/40 border border-emerald-500/30 flex items-center justify-between gap-3 text-xs text-emerald-200 animate-fade-in">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span>{dispatchSuccess}</span>
              </div>
              <button
                onClick={() => setDispatchSuccess(null)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {/* Proactive Low-Stock Triggers */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                Urgent Wholesale Replenishment Triggers ({triggers.length})
              </span>
              <button
                onClick={fetchInventoryStatus}
                className="text-[11px] text-slate-400 hover:text-slate-200 flex items-center gap-1 font-mono"
              >
                <RefreshCw className="w-3 h-3" />
                <span>Refresh</span>
              </button>
            </div>

            {triggers.length === 0 ? (
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-center text-xs text-slate-500">
                All SKUs above threshold. No urgent wholesale reorders needed right now.
              </div>
            ) : (
              <div className="space-y-3">
                {triggers.map((trig) => (
                  <div
                    key={trig.sku_id}
                    className="p-4 rounded-xl bg-slate-950 border border-amber-500/30 space-y-3 shadow-md"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="text-sm font-bold text-white flex items-center gap-2">
                          <span>{trig.name_en}</span>
                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30 font-mono">
                            LOW: {trig.current_stock} {trig.unit}
                          </span>
                        </div>
                        <div className="text-xs text-slate-400 font-hindi mt-0.5">
                          {trig.name_hi}
                        </div>
                      </div>

                      <div className="text-right">
                        <div className="text-xs font-mono font-bold text-amber-400">
                          ₹{trig.total_wholesale_cost_inr}
                        </div>
                        <div className="text-[10px] text-slate-500 font-mono">
                          @ ₹{trig.wholesale_rate_inr}/{trig.unit}
                        </div>
                      </div>
                    </div>

                    <p className="text-xs text-slate-300 font-hindi bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
                      "{trig.spoken_alert_hi}"
                    </p>

                    <div className="flex items-center justify-between gap-2 pt-1">
                      <div className="text-[11px] text-slate-400 flex items-center gap-1">
                        <Truck className="w-3.5 h-3.5 text-teal-400" />
                        <span>Supplier: <strong>{trig.wholesaler_name}</strong></span>
                      </div>

                      <button
                        onClick={() => dispatchMandiOrder(trig)}
                        className="px-3 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold flex items-center gap-1.5 shadow transition"
                      >
                        <Send className="w-3.5 h-3.5" />
                        <span>Send WhatsApp PO</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Full Catalogue Stock Grid */}
          <div className="space-y-3">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider px-1">
              Store Stock Overview ({inventoryItems.length} SKUs)
            </span>

            <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden text-xs">
              <table className="w-full text-left text-slate-300">
                <thead className="bg-slate-900 text-slate-400 font-semibold border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Item & SKU</th>
                    <th className="py-2.5 px-2 text-center">Stock</th>
                    <th className="py-2.5 px-2 text-right">Retail Rate</th>
                    <th className="py-2.5 px-3 text-right">Wholesale Rate</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {inventoryItems.map((item) => (
                    <tr key={item.sku_id} className="hover:bg-slate-900/40">
                      <td className="py-2 px-3">
                        <div className="font-semibold text-white">{item.name_en}</div>
                        <div className="text-[10px] text-slate-500 font-mono">{item.sku_id}</div>
                      </td>
                      <td className="py-2 px-2 text-center">
                        <span
                          className={`px-2 py-0.5 rounded text-[11px] font-mono font-bold ${
                            item.is_low_stock
                              ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                              : "text-slate-300"
                          }`}
                        >
                          {item.current_stock} {item.unit}
                        </span>
                      </td>
                      <td className="py-2 px-2 text-right text-slate-300 font-mono">
                        ₹{item.retail_price_inr}
                      </td>
                      <td className="py-2 px-3 text-right text-teal-400 font-mono font-medium">
                        ₹{item.wholesale_rate_inr}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950 flex items-center justify-between text-xs text-slate-500">
          <span>APMC Grain Mandi Connectivity • Wholesale Supply Rail</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
