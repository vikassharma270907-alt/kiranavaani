import React, { useState, useEffect } from "react";
import { X, Copy, Check, Download, Layers, ShieldCheck, ArrowRight, ExternalLink } from "lucide-react";
import { CartItem } from "./ShoppingCart";

interface ONDCModalProps {
  isOpen: boolean;
  onClose: () => void;
  cartItems: CartItem[];
  apiBaseUrl: string;
}

export const ONDCModal: React.FC<ONDCModalProps> = ({
  isOpen,
  onClose,
  cartItems,
  apiBaseUrl
}) => {
  const [ondcPayload, setOndcPayload] = useState<any>(null);
  const [isCopied, setIsCopied] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchOndcPayload();
    }
  }, [isOpen, cartItems]);

  const fetchOndcPayload = async () => {
    setIsLoading(true);
    try {
      const inputs = cartItems.map((it) => ({
        sku_id: it.sku_id,
        quantity: it.quantity,
        unit: it.unit
      }));

      const res = await fetch(`${apiBaseUrl}/ondc/export-beckn`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          bap_id: "nic2004:52110",
          customer_name: "Sharma Ji",
          delivery_address: "402 Shanti Kunj, Main Market, Delhi - 110001"
        })
      });

      if (res.ok) {
        const data = await res.json();
        setOndcPayload(data.payload);
      }
    } catch (e) {
      console.warn("Failed to fetch ONDC payload from backend, using local generator:", e);
      // Fallback local Beckn JSON
      setOndcPayload({
        context: {
          domain: "ONDC:RET10",
          country: "IND",
          city: "std:011",
          action: "confirm",
          core_version: "1.2.0",
          bap_id: "buyer-app.ondc.org",
          bpp_id: "kiranavaani.gnani.ai",
          timestamp: new Date().toISOString()
        },
        message: {
          order: {
            id: "ONDC-KRN-4892A1",
            state: "Created",
            provider: {
              id: "BPP-GUPTA-KIRANA-01",
              descriptor: { name: "Gupta Kirana & General Store" }
            },
            items: cartItems.map((it) => ({
              id: it.sku_id,
              descriptor: { name: it.name_en, short_desc: it.name_hi },
              quantity: { count: it.quantity, measure: { unit: it.unit, value: String(it.quantity) } },
              price: { currency: "INR", value: String(it.line_total) }
            })),
            quote: {
              price: { currency: "INR", value: String(cartItems.reduce((acc, it) => acc + it.line_total, 0)) }
            }
          }
        }
      });
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (!ondcPayload) return;
    navigator.clipboard.writeText(JSON.stringify(ondcPayload, null, 2));
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  const downloadJson = () => {
    if (!ondcPayload) return;
    const blob = new Blob([JSON.stringify(ondcPayload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ondc_beckn_order_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-sky-500/20 text-sky-400 flex items-center justify-center">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white">
                  ONDC Beckn Protocol Export
                </h2>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-sky-500/20 text-sky-300 border border-sky-500/30 font-mono">
                  v1.2.0 RET10 Grocery
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Converts spoken kirana phone orders into interoperable ONDC network transactions
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Banner */}
        <div className="p-3 bg-sky-950/30 border-b border-sky-500/20 text-xs text-sky-200 flex items-center justify-between gap-2">
          <span>
            🇮🇳 <strong>Digital India Rail:</strong> Seamless bridge between 12 million traditional offline kiranas and India's national Open Network for Digital Commerce.
          </span>
          <div className="flex items-center gap-2 flex-shrink-0">
            <button
              onClick={copyToClipboard}
              className="px-2.5 py-1 rounded bg-sky-600 hover:bg-sky-500 text-white font-medium text-xs flex items-center gap-1.5 transition-colors"
            >
              {isCopied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
              {isCopied ? "Copied!" : "Copy JSON"}
            </button>
            <button
              onClick={downloadJson}
              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-xs flex items-center gap-1.5 border border-slate-700"
            >
              <Download className="w-3.5 h-3.5" />
              Download
            </button>
          </div>
        </div>

        {/* JSON Viewer */}
        <div className="flex-1 overflow-y-auto p-4 bg-slate-950">
          <pre className="text-[11px] font-mono text-teal-300 whitespace-pre leading-relaxed overflow-x-auto">
            {JSON.stringify(ondcPayload, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
};
