import React, { useState, useRef, useEffect } from "react";
import { 
  CheckCircle2, 
  Play, 
  Pause, 
  Volume2, 
  CreditCard, 
  Share2, 
  QrCode, 
  BookOpen, 
  Copy, 
  Check, 
  ExternalLink,
  Receipt,
  Printer
} from "lucide-react";
import { CartItem } from "./ShoppingCart";
import { ThermalReceiptModal } from "./ThermalReceiptModal";
import { SoundboxChime } from "./SoundboxChime";

export interface KhataInfo {
  is_khata: boolean;
  customer_name?: string;
  khata_id?: string;
  previous_balance_inr: number;
  current_order_inr: number;
  new_balance_inr: number;
  payment_mode: string;
  note_hi?: string;
}

interface OrderSummaryProps {
  subtotal: number;
  deliveryFee: number;
  total: number;
  itemCount: number;
  items?: CartItem[];
  khataInfo?: KhataInfo | null;
  spokenReplyHi?: string;
  spokenReplyEn?: string;
  voiceAudioBase64?: string;
  voiceAudioFormat?: string;
  isMockTts?: boolean;
  onConfirmOrder: () => void;
  isOrderConfirmed: boolean;
  onOpenOndcModal?: () => void;
}

export const OrderSummary: React.FC<OrderSummaryProps> = ({
  subtotal,
  deliveryFee,
  total,
  itemCount,
  items = [],
  khataInfo,
  spokenReplyHi,
  spokenReplyEn,
  voiceAudioBase64,
  voiceAudioFormat = "wav",
  isMockTts = false,
  onConfirmOrder,
  isOrderConfirmed,
  onOpenOndcModal,
}) => {
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [selectedPaymentMode, setSelectedPaymentMode] = useState<"cod" | "upi" | "khata">(
    khataInfo?.is_khata ? "khata" : "cod"
  );
  const [isCopiedSlip, setIsCopiedSlip] = useState(false);
  const [showWhatsAppSlip, setShowWhatsAppSlip] = useState(false);
  const [showThermalReceipt, setShowThermalReceipt] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Sync payment mode if Khata is detected
  useEffect(() => {
    if (khataInfo?.is_khata) {
      setSelectedPaymentMode("khata");
    }
  }, [khataInfo]);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPlayingAudio(false);
    }

    if (voiceAudioBase64) {
      const mime = voiceAudioFormat === "mp3" ? "audio/mp3" : "audio/wav";
      const audioUrl = `data:${mime};base64,${voiceAudioBase64}`;
      const audio = new Audio(audioUrl);
      audioRef.current = audio;

      audio.onended = () => {
        setIsPlayingAudio(false);
      };
      audio.onerror = (e) => {
        console.warn("Audio element playback error:", e);
        setIsPlayingAudio(false);
      };
    }

    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
      }
    };
  }, [voiceAudioBase64, voiceAudioFormat]);

  const togglePlayback = () => {
    if (!audioRef.current) return;
    if (isPlayingAudio) {
      audioRef.current.pause();
      setIsPlayingAudio(false);
    } else {
      audioRef.current.play().then(() => {
        setIsPlayingAudio(true);
      }).catch((err) => {
        console.warn("Audio play prevented:", err);
      });
    }
  };

  // Generate authentic WhatsApp Receipt Slip Text
  const generateWhatsAppSlip = () => {
    const itemsLines = items.map((it, idx) => 
      `${idx + 1}. ${it.name_en} (${it.quantity} ${it.unit}) — ₹${it.line_total.toFixed(2)}`
    ).join("\n");

    const paymentLabel = 
      selectedPaymentMode === "khata" 
        ? `📖 खाता लेजर (${khataInfo?.customer_name || "Sharma Ji"}) • बकाया: ₹${(khataInfo?.new_balance_inr || total + 420).toFixed(2)}`
        : selectedPaymentMode === "upi" 
        ? "📱 UPI डिजिटल भुगतान (Pre-paid)" 
        : "💵 Cash on Delivery (नकद)";

    return (
`🛒 *गुप्ता किराना एवं जनरल स्टोर*
📍 दुकान नं. 4, मेन मार्केट, नई दिल्ली
━━━━━━━━━━━━━━━━━━━━━━
📋 *ग्राहक ऑर्डर पर्ची (Kirana Slip):*
${itemsLines || "1. किराना सामान"}
━━━━━━━━━━━━━━━━━━━━━━
💰 *कुल बिल (Total):* ₹${total.toFixed(2)}
🚚 *डिलीवरी:* मुफ़्त लोकल डिलीवरी (30 मिनट)
💳 *भुगतान प्रकार:* ${paymentLabel}
📲 *UPI से भुगतान करें:* upi://pay?pa=guptakirana@okaxis&pn=GuptaKiranaStore&am=${total.toFixed(2)}&cu=INR

_किरानावाणी (KiranaVaani) वॉयस AI द्वारा जेनरेट किया गया_`
    );
  };

  const handleCopySlip = () => {
    const text = generateWhatsAppSlip();
    navigator.clipboard.writeText(text);
    setIsCopiedSlip(true);
    setTimeout(() => setIsCopiedSlip(false), 2000);
  };

  const handleShareWhatsApp = () => {
    const text = generateWhatsAppSlip();
    const url = `https://wa.me/?text=${encodeURIComponent(text)}`;
    window.open(url, "_blank");
  };

  const upiUrl = `upi://pay?pa=guptakirana@okaxis&pn=Gupta+Kirana+Store&am=${total.toFixed(2)}&cu=INR`;
  const qrCodeImgUrl = `https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=${encodeURIComponent(upiUrl)}&color=0284c7&bgcolor=030712`;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <CreditCard className="w-5 h-5 text-sky-400" />
          Billing & Kirana Ledger
        </h2>
        <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
          {itemCount} Items
        </span>
      </div>

      {/* Bill Calculation Rows */}
      <div className="space-y-2 text-xs">
        <div className="flex justify-between text-slate-300">
          <span>Items Subtotal:</span>
          <span className="font-mono text-slate-100">₹{subtotal.toFixed(2)}</span>
        </div>
        <div className="flex justify-between text-slate-300">
          <span>Kirana Local Delivery (30 mins):</span>
          <span className="text-teal-400 font-medium">
            {deliveryFee === 0 ? "FREE" : `₹${deliveryFee.toFixed(2)}`}
          </span>
        </div>
        <div className="pt-2 border-t border-slate-800 flex justify-between items-baseline">
          <span className="text-sm font-bold text-white">Total Amount (कुल राशि):</span>
          <span className="text-xl font-bold font-mono text-teal-300">₹{total.toFixed(2)}</span>
        </div>
      </div>

      {/* Kirana Khata (खाता लेजर) Section if detected */}
      {khataInfo && khataInfo.is_khata && (
        <div className="p-3.5 bg-gradient-to-r from-amber-950/40 to-slate-950/80 rounded-xl border border-amber-500/40 space-y-2 shadow-inner">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-xs font-bold text-amber-300">
              <BookOpen className="w-4 h-4 text-amber-400" />
              किराना खाता बही (Khata Credit Ledger)
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40 font-mono">
              Account {khataInfo.khata_id || "#42"}
            </span>
          </div>

          <div className="text-xs text-slate-200">
            Customer: <strong className="text-white">{khataInfo.customer_name}</strong>
          </div>

          <div className="grid grid-cols-3 gap-2 pt-1 text-[11px] font-mono border-t border-amber-500/20">
            <div>
              <div className="text-slate-400 text-[10px]">Previous Due:</div>
              <div className="text-slate-200 font-semibold">₹{khataInfo.previous_balance_inr.toFixed(2)}</div>
            </div>
            <div>
              <div className="text-slate-400 text-[10px]">This Order:</div>
              <div className="text-amber-400 font-semibold">+₹{total.toFixed(2)}</div>
            </div>
            <div>
              <div className="text-slate-400 text-[10px]">New Balance:</div>
              <div className="text-rose-400 font-bold">
                ₹{(khataInfo.previous_balance_inr + total).toFixed(2)}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Payment Method Selector */}
      <div className="space-y-1.5 pt-1">
        <label className="text-xs font-semibold text-slate-300">Payment Channel (भुगतान का माध्यम):</label>
        <div className="grid grid-cols-3 gap-1.5 text-xs">
          <button
            onClick={() => setSelectedPaymentMode("cod")}
            className={`py-1.5 px-2 rounded-lg border text-center transition-all ${
              selectedPaymentMode === "cod"
                ? "bg-sky-500/15 border-sky-500 text-sky-200 font-semibold"
                : "bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-200"
            }`}
          >
            💵 Cash (COD)
          </button>
          <button
            onClick={() => setSelectedPaymentMode("upi")}
            className={`py-1.5 px-2 rounded-lg border text-center transition-all ${
              selectedPaymentMode === "upi"
                ? "bg-sky-500/15 border-sky-500 text-sky-200 font-semibold"
                : "bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-200"
            }`}
          >
            📱 UPI QR
          </button>
          <button
            onClick={() => setSelectedPaymentMode("khata")}
            className={`py-1.5 px-2 rounded-lg border text-center transition-all ${
              selectedPaymentMode === "khata"
                ? "bg-amber-500/15 border-amber-500 text-amber-200 font-semibold"
                : "bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-200"
            }`}
          >
            📖 Store Khata
          </button>
        </div>
      </div>

      {/* Dynamic UPI QR Code View */}
      {selectedPaymentMode === "upi" && total > 0 && (
        <div className="p-3 bg-slate-950 rounded-xl border border-sky-500/30 flex flex-col items-center justify-center space-y-2">
          <div className="text-xs font-semibold text-sky-300 flex items-center gap-1.5">
            <QrCode className="w-4 h-4 text-sky-400" />
            Scan to Pay ₹{total.toFixed(2)} via UPI
          </div>

          <div className="p-2 bg-white rounded-lg shadow-md">
            <img 
              src={qrCodeImgUrl} 
              alt="UPI Payment QR Code" 
              className="w-32 h-32 block object-contain"
              onError={(e) => {
                // Fallback placeholder if offline
                (e.target as HTMLElement).style.display = "none";
              }}
            />
          </div>

          <div className="text-[10px] text-slate-400 text-center font-mono">
            VPA: <span className="text-sky-300">guptakirana@okaxis</span>
            <div className="text-[9px] text-slate-500 mt-0.5">Supports Google Pay • PhonePe • Paytm • BHIM</div>
          </div>
        </div>
      )}

      {/* Timbre v2.5 Spoken Voice Readback */}
      {(spokenReplyHi || voiceAudioBase64) && (
        <div className="p-3.5 bg-slate-950/90 rounded-lg border border-sky-500/20 space-y-2.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-sky-300">
              <Volume2 className="w-4 h-4 text-sky-400" />
              Gnani Timbre v2.5 Voice Readback
            </div>
            <span
              className={`text-[10px] px-2 py-0.5 rounded-full border ${
                isMockTts
                  ? "bg-amber-500/10 text-amber-300 border-amber-500/20"
                  : "bg-emerald-500/10 text-emerald-300 border-emerald-500/20"
              }`}
            >
              {isMockTts ? "Demo Tone" : "Live Timbre Audio"}
            </span>
          </div>

          {spokenReplyHi && (
            <div className="text-xs text-slate-200 italic font-hindi leading-relaxed">
              "{spokenReplyHi}"
            </div>
          )}

          {voiceAudioBase64 && (
            <button
              onClick={togglePlayback}
              className="w-full py-2 px-3 rounded-lg bg-sky-500/15 hover:bg-sky-500/25 border border-sky-500/30 text-sky-200 text-xs font-medium flex items-center justify-center gap-2 transition-all"
            >
              {isPlayingAudio ? (
                <>
                  <Pause className="w-4 h-4 text-sky-400 animate-pulse" />
                  Playing Voice Confirmation...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 text-sky-400" />
                  Play Spoken Readback (Timbre TTS)
                </>
              )}
            </button>
          )}
        </div>
      )}

      {/* WhatsApp Kirana Receipt Slip Generator */}
      <div className="space-y-2 pt-1 border-t border-slate-800">
        <button
          onClick={() => setShowWhatsAppSlip((prev) => !prev)}
          className="w-full py-2 px-3 rounded-lg bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 text-slate-200 text-xs font-medium flex items-center justify-between transition-colors"
        >
          <span className="flex items-center gap-1.5">
            <Receipt className="w-4 h-4 text-teal-400" />
            WhatsApp Kirana Order Slip (रसीद)
          </span>
          <span className="text-[10px] text-teal-400 font-mono">
            {showWhatsAppSlip ? "Hide Slip ▲" : "View Slip ▼"}
          </span>
        </button>

        {showWhatsAppSlip && (
          <div className="p-3 bg-slate-950 rounded-xl border border-teal-500/30 space-y-2.5 text-xs">
            <pre className="font-mono text-[11px] text-slate-300 whitespace-pre-wrap bg-slate-900 p-2.5 rounded-lg border border-slate-800 overflow-x-auto leading-relaxed">
              {generateWhatsAppSlip()}
            </pre>

            <div className="flex items-center gap-2">
              <button
                onClick={handleShareWhatsApp}
                className="flex-1 py-1.5 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs flex items-center justify-center gap-1.5 shadow transition-colors"
              >
                <Share2 className="w-3.5 h-3.5" />
                Share on WhatsApp
              </button>
              <button
                onClick={handleCopySlip}
                className="py-1.5 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs border border-slate-700 flex items-center gap-1 transition-colors"
              >
                {isCopiedSlip ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{isCopiedSlip ? "Copied!" : "Copy"}</span>
              </button>
            </div>
          </div>
        )}

        {/* 58mm Thermal POS Receipt Button */}
        {items.length > 0 && (
          <button
            onClick={() => setShowThermalReceipt(true)}
            className="w-full py-2 px-3 rounded-lg bg-amber-950/30 hover:bg-amber-900/40 border border-amber-500/30 text-amber-200 text-xs font-semibold flex items-center justify-between transition-colors group"
          >
            <span className="flex items-center gap-1.5">
              <Printer className="w-4 h-4 text-amber-400" />
              58mm Thermal POS Receipt (दुकान रसीद)
            </span>
            <span className="text-[10px] text-amber-400 font-mono group-hover:translate-x-0.5 transition-transform">
              Print / Preview &rarr;
            </span>
          </button>
        )}

        {/* ONDC Beckn Protocol Export Button */}
        {onOpenOndcModal && items.length > 0 && (
          <button
            onClick={onOpenOndcModal}
            className="w-full py-2 px-3 rounded-lg bg-sky-950/40 hover:bg-sky-900/40 border border-sky-500/30 text-sky-200 text-xs font-semibold flex items-center justify-between transition-colors group"
          >
            <span className="flex items-center gap-1.5">
              <span className="text-base">🇮🇳</span>
              Export to ONDC (Beckn Protocol v1.2.0)
            </span>
            <span className="text-[10px] text-sky-400 font-mono group-hover:translate-x-0.5 transition-transform">
              View JSON &rarr;
            </span>
          </button>
        )}
      </div>

      {/* Confirm order action */}
      <div className="pt-2">
        {isOrderConfirmed ? (
          <div className="space-y-3">
            <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg flex items-center justify-center gap-2 text-emerald-300 text-xs font-semibold">
              <CheckCircle2 className="w-4 h-4" />
              Order Confirmed & Sent to Kirana Store!
            </div>
            <SoundboxChime
              amount={total}
              customerName={khataInfo?.customer_name || "Customer"}
              paymentMode={selectedPaymentMode.toUpperCase()}
              autoPlayTrigger={true}
            />
          </div>
        ) : (
          <button
            onClick={onConfirmOrder}
            disabled={itemCount === 0}
            className={`w-full py-3 px-4 rounded-xl font-semibold text-sm transition-all shadow-lg flex items-center justify-center gap-2 ${
              itemCount === 0
                ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                : "bg-gradient-to-r from-teal-500 to-sky-500 hover:from-teal-400 hover:to-sky-400 text-white shadow-sky-500/20 active:scale-95"
            }`}
          >
            <CheckCircle2 className="w-4 h-4" />
            Confirm Order (₹{total.toFixed(2)})
          </button>
        )}
      </div>

      {/* 58mm Thermal Receipt Printable Modal */}
      <ThermalReceiptModal
        isOpen={showThermalReceipt}
        onClose={() => setShowThermalReceipt(false)}
        items={items}
        subtotal={subtotal}
        total={total}
        customerName={khataInfo?.customer_name}
        paymentMode={selectedPaymentMode.toUpperCase()}
      />
    </div>
  );
};
