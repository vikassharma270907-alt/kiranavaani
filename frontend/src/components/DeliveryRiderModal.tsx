import React, { useState, useEffect, useRef } from "react";
import { 
  X, 
  Truck, 
  MapPin, 
  Clock, 
  Phone, 
  Volume2, 
  CheckCircle2, 
  Share2, 
  Send, 
  ShieldCheck, 
  FileText,
  Navigation
} from "lucide-react";
import { CartItem } from "./ShoppingCart";

interface DeliveryRiderModalProps {
  isOpen: boolean;
  onClose: () => void;
  apiBaseUrl: string;
  cartItems: CartItem[];
  totalAmount: number;
  customerName?: string;
  transcript?: string;
  landmarkInfo?: any;
}

export const DeliveryRiderModal: React.FC<DeliveryRiderModalProps> = ({
  isOpen,
  onClose,
  apiBaseUrl,
  cartItems,
  totalAmount,
  customerName = "Sharma Ji (शर्मा जी)",
  transcript = "",
  landmarkInfo
}) => {
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [dispatchData, setDispatchData] = useState<any | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [deliveryStatus, setDeliveryStatus] = useState<string>("PACKED");

  useEffect(() => {
    if (isOpen) {
      handleGenerateDispatchSlip();
    }
  }, [isOpen]);

  const handleGenerateDispatchSlip = async () => {
    setIsLoading(true);
    try {
      const itemsPayload = cartItems.map((it) => ({
        sku_id: it.sku_id,
        quantity: it.quantity,
        unit: it.unit
      }));

      const res = await fetch(`${apiBaseUrl}/delivery/dispatch-rider`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer_name: customerName,
          transcript: transcript || "Bhaiya delivery Ram Mandir ke peeche, teesri gali me peela makaan, second floor pe bhej dena shaam 6 baje",
          total_amount_inr: totalAmount || 465.0,
          cart_items: itemsPayload,
          landmark_info: landmarkInfo
        })
      });

      if (res.ok) {
        const data = await res.json();
        setDispatchData(data);
      }
    } catch (e) {
      console.warn("Rider dispatch error:", e);
    } finally {
      setIsLoading(false);
    }
  };

  const playRiderVoiceNote = () => {
    if (dispatchData?.voice_audio_base64) {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }
      const audio = new Audio(`data:audio/${dispatchData.voice_audio_format || "wav"};base64,${dispatchData.voice_audio_base64}`);
      audioRef.current = audio;
      audio.play().catch((e) => console.warn("Voice note play error:", e));
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
      <div className="w-full max-w-2xl bg-slate-900 border border-emerald-500/40 rounded-2xl shadow-2xl shadow-emerald-500/10 overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-4 bg-gradient-to-r from-emerald-950/60 to-slate-900 border-b border-emerald-500/30 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-300">
              <Truck className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white tracking-tight">
                  Chhotu Dispatch (किराना डिलीवरी राइडर)
                </h3>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/30">
                  LANDMARK NER
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Spoken Indian street landmark extraction & WhatsApp rider voice task card
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
          {/* Live Delivery Status Timeline */}
          <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400 font-medium">Delivery Status Tracking:</span>
              <span className="font-mono text-emerald-400 font-bold">
                {deliveryStatus === "PACKED" ? "📦 ORDER PACKED" : deliveryStatus === "DISPATCHED" ? "🛵 OUT FOR DELIVERY" : "✅ DELIVERED"}
              </span>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setDeliveryStatus("PACKED")}
                className={`flex-1 py-1 text-[11px] rounded font-semibold border transition-all ${
                  deliveryStatus === "PACKED"
                    ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                    : "bg-slate-800 text-slate-400 border-slate-700"
                }`}
              >
                1. Packed
              </button>
              <button
                onClick={() => setDeliveryStatus("DISPATCHED")}
                className={`flex-1 py-1 text-[11px] rounded font-semibold border transition-all ${
                  deliveryStatus === "DISPATCHED"
                    ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                    : "bg-slate-800 text-slate-400 border-slate-700"
                }`}
              >
                2. Out for Delivery
              </button>
              <button
                onClick={() => setDeliveryStatus("DELIVERED")}
                className={`flex-1 py-1 text-[11px] rounded font-semibold border transition-all ${
                  deliveryStatus === "DELIVERED"
                    ? "bg-teal-500/20 text-teal-300 border-teal-500/40"
                    : "bg-slate-800 text-slate-400 border-slate-700"
                }`}
              >
                3. Delivered
              </button>
            </div>
          </div>

          {/* Extracted Vernacular Landmark Navigation Card */}
          <div className="p-4 rounded-xl bg-slate-950/80 border border-emerald-500/30 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-emerald-300 uppercase tracking-wide flex items-center gap-1.5">
                <Navigation className="w-3.5 h-3.5" />
                Spoken Landmark Route Directions (Vernacular NER)
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                {dispatchData?.dispatch_id || "RIDER-042"}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                <div className="text-[10px] text-slate-400 uppercase tracking-wider flex items-center gap-1">
                  <MapPin className="w-3 h-3 text-rose-400" />
                  Primary Landmark & Street Marker
                </div>
                <div className="text-sm font-bold text-white font-hindi">
                  {dispatchData?.vernacular_route_directions || "राम मंदिर के पीछे, 3री गली, पीला मकान"}
                </div>
              </div>

              <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                <div className="text-[10px] text-slate-400 uppercase tracking-wider flex items-center gap-1">
                  <Clock className="w-3 h-3 text-sky-400" />
                  Delivery Window & Recipient
                </div>
                <div className="text-sm font-bold text-white font-hindi">
                  {dispatchData?.customer_name || customerName} • {dispatchData?.delivery_window || "शाम 6:00 बजे"}
                </div>
              </div>
            </div>

            {/* Payment Directive Card */}
            <div className="p-2.5 rounded-lg bg-emerald-950/30 border border-emerald-500/30 flex items-center justify-between text-xs">
              <span className="text-slate-300 font-medium">Payment Collection Directive:</span>
              <span className="text-emerald-300 font-bold font-hindi">
                {dispatchData?.payment_collection_directive || "नकद ₹465 लेना है (Cash on Delivery)"}
              </span>
            </div>
          </div>

          {/* Timbre Spoken Voice Note for Rider */}
          {dispatchData?.rider_voice_note_hi && (
            <div className="p-4 rounded-xl bg-gradient-to-r from-emerald-950/40 to-slate-950 border border-emerald-500/30 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-emerald-300 uppercase tracking-wide flex items-center gap-1.5">
                  <Volume2 className="w-3.5 h-3.5" />
                  छोटू के लिए वॉइस नोट (Timbre TTS Spoken Briefing):
                </span>
                {dispatchData.voice_audio_base64 && (
                  <button
                    onClick={playRiderVoiceNote}
                    className="p-1 rounded bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/30 transition-colors flex items-center gap-1 text-[11px] px-2 font-bold"
                  >
                    <Volume2 className="w-3.5 h-3.5" />
                    <span>Play Audio</span>
                  </button>
                )}
              </div>
              <p className="text-xs text-slate-200 font-hindi italic leading-relaxed">
                "{dispatchData.rider_voice_note_hi}"
              </p>
            </div>
          )}

          {/* WhatsApp Slip Preview */}
          {dispatchData?.whatsapp_rider_text && (
            <div className="space-y-1.5">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                Formatted WhatsApp Rider Slip:
              </span>
              <pre className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] font-mono text-emerald-300/90 whitespace-pre-wrap leading-relaxed">
                {dispatchData.whatsapp_rider_text}
              </pre>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-4 bg-slate-950 border-t border-slate-800 flex items-center justify-between gap-3">
          <button
            onClick={() => handleGenerateDispatchSlip()}
            disabled={isLoading}
            className="px-3 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
          >
            Refresh Route NER
          </button>

          <a
            href={dispatchData?.whatsapp_url || "https://wa.me/919811122334"}
            target="_blank"
            rel="noopener noreferrer"
            className="px-5 py-2 rounded-xl text-xs font-bold bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-slate-950 flex items-center gap-2 shadow-lg shadow-emerald-500/20 transition-all"
          >
            <Send className="w-4 h-4 fill-current" />
            <span>1-Click Dispatch via WhatsApp to Chhotu</span>
          </a>
        </div>
      </div>
    </div>
  );
};

