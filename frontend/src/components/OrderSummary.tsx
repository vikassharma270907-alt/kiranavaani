import React, { useState, useRef, useEffect } from "react";
import { CheckCircle2, Play, Pause, Volume2, ShieldCheck, Sparkles, CreditCard } from "lucide-react";

interface OrderSummaryProps {
  subtotal: number;
  deliveryFee: number;
  total: number;
  itemCount: number;
  spokenReplyHi?: string;
  spokenReplyEn?: string;
  voiceAudioBase64?: string;
  voiceAudioFormat?: string;
  isMockTts?: boolean;
  onConfirmOrder: () => void;
  isOrderConfirmed: boolean;
}

export const OrderSummary: React.FC<OrderSummaryProps> = ({
  subtotal,
  deliveryFee,
  total,
  itemCount,
  spokenReplyHi,
  spokenReplyEn,
  voiceAudioBase64,
  voiceAudioFormat = "wav",
  isMockTts = false,
  onConfirmOrder,
  isOrderConfirmed,
}) => {
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    // Stop any existing audio
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPlayingAudio(false);
    }

    // When a new voice audio payload arrives, initialize audio element
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

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <CreditCard className="w-5 h-5 text-sky-400" />
          Billing & Voice Confirmation
        </h2>
        <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
          {itemCount} Items
        </span>
      </div>

      {/* Bill calculation rows */}
      <div className="space-y-2 text-xs">
        <div className="flex justify-between text-slate-300">
          <span>Items Subtotal:</span>
          <span className="font-mono text-slate-100">₹{subtotal.toFixed(2)}</span>
        </div>
        <div className="flex justify-between text-slate-300">
          <span>Kirana Local Delivery:</span>
          <span className="text-teal-400 font-medium">
            {deliveryFee === 0 ? "FREE" : `₹${deliveryFee.toFixed(2)}`}
          </span>
        </div>
        <div className="pt-2 border-t border-slate-800 flex justify-between items-baseline">
          <span className="text-sm font-bold text-white">Total Amount (कुल):</span>
          <span className="text-xl font-bold font-mono text-teal-300">₹{total.toFixed(2)}</span>
        </div>
      </div>

      {/* Spoken voice readback section */}
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
                  Playing Voice Readback...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 text-sky-400" />
                  Listen to Spoken Readback (Timbre TTS)
                </>
              )}
            </button>
          )}
        </div>
      )}

      {/* Confirm order action */}
      <div className="pt-2">
        {isOrderConfirmed ? (
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg flex items-center justify-center gap-2 text-emerald-300 text-xs font-semibold">
            <CheckCircle2 className="w-4 h-4" />
            Order Confirmed & Sent to Kirana Store!
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
    </div>
  );
};
