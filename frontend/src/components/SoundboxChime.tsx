import React, { useState, useRef } from "react";
import { Volume2, Play, Sparkles, Radio, CheckCircle2, ShieldCheck } from "lucide-react";

interface SoundboxChimeProps {
  amount: number;
  customerName?: string;
  paymentMode?: string;
  autoPlayTrigger?: boolean;
}

export const SoundboxChime: React.FC<SoundboxChimeProps> = ({
  amount,
  customerName = "Sharma Ji",
  paymentMode = "UPI",
  autoPlayTrigger = false
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [lastChimeText, setLastChimeText] = useState("");
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const playSoundboxAlert = async () => {
    if (isPlaying) return;
    setIsPlaying(true);

    try {
      const res = await fetch("/soundbox-chime", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          amount_inr: amount > 0 ? amount : 106.0,
          store_name: "Gupta Kirana Store",
          customer_name: customerName,
          payment_mode: paymentMode
        })
      });

      if (res.ok) {
        const data = await res.json();
        setLastChimeText(data.chime_text_hi);

        if (data.voice_audio_base64) {
          const audio = new Audio(`data:audio/${data.voice_audio_format || "wav"};base64,${data.voice_audio_base64}`);
          audioRef.current = audio;
          audio.onended = () => setIsPlaying(false);
          audio.onerror = () => setIsPlaying(false);
          await audio.play();
          return;
        }
      }
    } catch (err) {
      console.warn("Soundbox chime fallback:", err);
    }

    // Fallback simulated chime speech via Web Speech Synthesis if backend is offline
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      const text = `गुप्ता किराना साउंडबॉक्स: ${Math.round(amount || 106)} रुपये का यूपीआई भुगतान प्राप्त हुआ`;
      setLastChimeText(text);
      const utter = new SpeechSynthesisUtterance(text);
      utter.lang = "hi-IN";
      utter.rate = 0.95;
      utter.onend = () => setIsPlaying(false);
      utter.onerror = () => setIsPlaying(false);
      window.speechSynthesis.speak(utter);
    } else {
      setTimeout(() => setIsPlaying(false), 2000);
    }
  };

  return (
    <div className="bg-gradient-to-br from-blue-950/80 via-slate-900 to-slate-950 border border-blue-800/40 rounded-xl p-3.5 shadow-xl flex items-center justify-between gap-3 relative overflow-hidden">
      {/* Background Accent Glow */}
      <div className="absolute -right-6 -bottom-6 w-24 h-24 bg-blue-500/10 rounded-full blur-xl pointer-events-none" />

      {/* Soundbox Device Avatar */}
      <div className="flex items-center gap-3">
        <div className="relative">
          <div className="w-10 h-10 rounded-lg bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400 shadow-inner">
            <Radio className="w-5 h-5 animate-pulse" />
          </div>
          {/* Active LED Light */}
          <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-400 rounded-full shadow-[0_0_8px_#34d399]" />
        </div>

        <div>
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-bold text-white tracking-wide">
              Kirana Soundbox 2.0
            </span>
            <span className="text-[10px] px-1.5 py-0.2 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30 font-medium">
              Paytm / PhonePe Style
            </span>
          </div>
          <div className="text-[11px] text-slate-400 font-hindi mt-0.5">
            {lastChimeText || "गुप्ता किराना साउंडबॉक्स तैयार है • वॉयस अलर्ट"}
          </div>
        </div>
      </div>

      {/* Chime Trigger Button */}
      <button
        onClick={playSoundboxAlert}
        disabled={isPlaying}
        className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all shadow-md ${
          isPlaying
            ? "bg-amber-500/20 text-amber-300 border border-amber-500/30 animate-pulse"
            : "bg-blue-600 hover:bg-blue-500 text-white hover:shadow-blue-500/25 active:scale-95"
        }`}
      >
        <Volume2 className="w-3.5 h-3.5" />
        {isPlaying ? "बोल रहा है..." : "Chime Test"}
      </button>
    </div>
  );
};
