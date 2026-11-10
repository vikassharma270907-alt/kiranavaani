import React, { useState, useEffect, useRef } from "react";
import {
  MessageSquare,
  X,
  Play,
  Pause,
  CheckCheck,
  Send,
  Zap,
  ShoppingBag,
  ExternalLink,
  QrCode,
  Sparkles,
  Phone,
  Mic,
  ArrowRight
} from "lucide-react";

export interface WhatsAppVoiceResponse {
  note_id: string;
  sender_name: string;
  sender_phone: string;
  received_timestamp: string;
  transcript: string;
  parsed_items: any[];
  confirmed_skus_count: number;
  cart_total_inr: number;
  estimated_delivery_mins: number;
  is_tatkal: boolean;
  upi_payment_link: string;
  upi_qr_data: string;
  whatsapp_auto_reply_text: string;
  voice_audio_base64?: string;
  voice_audio_format?: string;
}

interface WhatsAppVoiceModalProps {
  isOpen: boolean;
  onClose: () => void;
  apiBaseUrl: string;
  onImportToLiveCart?: (transcript: string) => void;
}

export const WhatsAppVoiceModal: React.FC<WhatsAppVoiceModalProps> = ({
  isOpen,
  onClose,
  apiBaseUrl,
  onImportToLiveCart
}) => {
  const [selectedPreset, setSelectedPreset] = useState<string>("snack_rush");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [result, setResult] = useState<WhatsAppVoiceResponse | null>(null);
  const [isPlayingIncoming, setIsPlayingIncoming] = useState<boolean>(false);
  const [isPlayingReply, setIsPlayingReply] = useState<boolean>(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  const presets = [
    {
      id: "snack_rush",
      label: "⚡ Urgent Snacks (Tatkal Priority)",
      spoken: "भैया 2 packet Maggi, 1 Madhur Sugar और आधा लीटर Amul दूध तुरंत भेज दो, पैसे UPI से कर दूंगा।",
      sender: "Sharma Ji (शर्मा जी)",
      phone: "+91 98201-12345",
      time: "05:14 PM",
      duration: "0:06"
    },
    {
      id: "breakfast_basket",
      label: "☕ Breakfast Combo (Tea + Butter + Biscuits)",
      spoken: "नमस्ते गुप्ता जी, 1 Tata Tea Gold, 1 Amul Butter और 2 Good Day बिस्कुट भेज देना।",
      sender: "Verma Ji (वर्मा जी)",
      phone: "+91 98111-88990",
      time: "07:30 AM",
      duration: "0:05"
    },
    {
      id: "evening_rashan",
      label: "🍲 Daily Staples (Rice + Dal + Mustard Oil)",
      spoken: "भैया 2 किलो बासमती चावल, 1 किलो तूर दाल और 1 लीटर सरसों तेल भेज देना, शाम 6 बजे।",
      sender: "Gupta Sahab (गुप्ता साहब)",
      phone: "+91 98333-22110",
      time: "04:45 PM",
      duration: "0:07"
    }
  ];

  const currentPresetObj = presets.find((p) => p.id === selectedPreset) || presets[0];

  const handleProcessVoiceNote = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${apiBaseUrl}/whatsapp/voice-note`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sender_name: currentPresetObj.sender,
          sender_phone: currentPresetObj.phone,
          preset_id: selectedPreset,
          keyterms_enabled: true
        })
      });
      if (res.ok) {
        const data = await res.json();
        setResult(data);
      }
    } catch (e) {
      console.error("WhatsApp voice note error:", e);
    } finally {
      setIsLoading(false);
    }
  };

  const playSyntheticTone = (isReply = false) => {
    if (audioRef.current) {
      audioRef.current.pause();
    }

    if (isReply && result?.voice_audio_base64) {
      const audio = new Audio(`data:audio/${result.voice_audio_format || "wav"};base64,${result.voice_audio_base64}`);
      audioRef.current = audio;
      setIsPlayingReply(true);
      audio.onended = () => setIsPlayingReply(false);
      audio.onerror = () => setIsPlayingReply(false);
      audio.play();
      return;
    }

    // Play pleasant confirmation audio chime
    try {
      const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(440, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.3);
      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.5);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.5);
      setIsPlayingIncoming(true);
      setTimeout(() => setIsPlayingIncoming(false), 500);
    } catch (e) {
      console.warn("WebAudio chime fallback:", e);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-2xl bg-slate-900 border border-emerald-500/30 rounded-2xl shadow-2xl flex flex-col max-h-[92vh] overflow-hidden">
        {/* WhatsApp-Style Header */}
        <div className="bg-[#075e54] text-white px-4 py-3 flex items-center justify-between border-b border-[#128c7e]/40">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-emerald-700 border border-emerald-400/40 flex items-center justify-center font-bold text-white shadow">
              <MessageSquare className="w-5 h-5 text-emerald-100" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <h2 className="text-sm font-bold text-white tracking-wide">
                  Gupta Kirana Order Desk
                </h2>
                <span className="text-[10px] bg-emerald-600/80 text-emerald-100 px-1.5 py-0.2 rounded font-mono">
                  WhatsApp Bot
                </span>
              </div>
              <p className="text-[11px] text-emerald-200/90 flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>Customer PTT Voice Note Ingestion • Online</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-emerald-800/60 hover:bg-emerald-800 text-emerald-100 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div className="p-4 sm:p-5 overflow-y-auto space-y-4 text-xs">
          {/* Bharat Reality Callout Banner */}
          <div className="p-3 rounded-xl bg-emerald-950/40 border border-emerald-500/20 text-slate-300 flex items-start gap-2.5">
            <Sparkles className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
            <div>
              <strong className="text-white">Why WhatsApp Voice Notes (PTT)?</strong> Over 80% of digital orders to neighbourhood kirana stores arrive as WhatsApp voice messages rather than live calls. KiranaVaani transcribes, decomposes into SKUs, and automatically replies with a dynamic UPI link & Timbre spoken voice note!
            </div>
          </div>

          {/* Preset Voice Note Selector */}
          <div>
            <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-2">
              Select Incoming WhatsApp Voice Note Preset:
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {presets.map((p) => (
                <button
                  key={p.id}
                  onClick={() => {
                    setSelectedPreset(p.id);
                    setResult(null);
                  }}
                  className={`p-2.5 rounded-xl border text-left transition-all ${
                    selectedPreset === p.id
                      ? "bg-emerald-500/10 border-emerald-500/50 text-white shadow-md shadow-emerald-500/10"
                      : "bg-slate-800/60 border-slate-700 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <div className="font-semibold text-xs text-emerald-300">{p.label}</div>
                  <div className="text-[10px] text-slate-500 mt-1">{p.sender} • {p.duration}</div>
                </button>
              ))}
            </div>
          </div>

          {/* WhatsApp Chat Simulation Container */}
          <div className="p-4 rounded-2xl bg-[#0b141a] border border-slate-800 space-y-3 shadow-inner">
            <div className="text-center">
              <span className="text-[10px] bg-slate-800/80 text-slate-400 px-2.5 py-0.5 rounded-md font-mono">
                TODAY • 100% SYNTHETIC ZERO PII
              </span>
            </div>

            {/* Incoming Customer Voice Message Bubble */}
            <div className="flex items-start gap-2 max-w-[85%]">
              <div className="bg-[#202c33] text-slate-200 p-3 rounded-2xl rounded-tl-sm border border-slate-700/50 shadow-md space-y-2 w-full">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="font-bold text-emerald-400">{currentPresetObj.sender}</span>
                  <span className="text-slate-500 text-[10px]">{currentPresetObj.phone}</span>
                </div>

                {/* Voice Note Audio Wave Player */}
                <div className="flex items-center gap-3 bg-[#111b21] p-2.5 rounded-xl border border-slate-800">
                  <button
                    onClick={() => playSyntheticTone(false)}
                    className="w-8 h-8 rounded-full bg-emerald-500 hover:bg-emerald-400 text-slate-950 flex items-center justify-center flex-shrink-0 transition-transform active:scale-95"
                  >
                    {isPlayingIncoming ? <Pause className="w-4 h-4 fill-current" /> : <Play className="w-4 h-4 fill-current ml-0.5" />}
                  </button>

                  <div className="flex-1 space-y-1">
                    <div className="flex items-center gap-1 h-4">
                      {[40, 75, 55, 90, 60, 85, 45, 95, 70, 50, 80, 65, 40, 90, 60, 45].map((h, i) => (
                        <div
                          key={i}
                          className={`w-1 rounded-full ${isPlayingIncoming ? "bg-emerald-400 animate-pulse" : "bg-emerald-600/70"}`}
                          style={{ height: `${h}%` }}
                        />
                      ))}
                    </div>
                    <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
                      <span>{currentPresetObj.duration}</span>
                      <Mic className="w-3 h-3 text-emerald-400" />
                    </div>
                  </div>
                </div>

                {/* Spoken transcript quote */}
                <p className="text-xs text-slate-300 italic border-l-2 border-emerald-500/40 pl-2 py-0.5">
                  "{currentPresetObj.spoken}"
                </p>

                <div className="text-right text-[10px] text-slate-500 flex items-center justify-end gap-1">
                  <span>{currentPresetObj.time}</span>
                  <CheckCheck className="w-3.5 h-3.5 text-sky-400" />
                </div>
              </div>
            </div>

            {/* Action Button: AI Ingest & Process Voice Note */}
            <div className="pt-2 flex justify-center">
              <button
                onClick={handleProcessVoiceNote}
                disabled={isLoading}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 flex items-center gap-2 shadow-lg shadow-emerald-500/20 transition-all disabled:opacity-50"
              >
                {isLoading ? (
                  <>
                    <span className="w-3.5 h-3.5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin"></span>
                    <span>Processing with Prisma v3.0 & Parser...</span>
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4 fill-current" />
                    <span>Run Speech AI & Generate WhatsApp Reply</span>
                  </>
                )}
              </button>
            </div>

            {/* Result: WhatsApp Interactive Order Slip & Bot Response */}
            {result && (
              <div className="flex items-end justify-end gap-2 pt-2 animate-fade-in">
                <div className="bg-[#005c4b] text-white p-3.5 rounded-2xl rounded-tr-sm shadow-xl max-w-[90%] space-y-3">
                  <div className="flex items-center justify-between text-[11px] pb-1 border-b border-emerald-400/30">
                    <span className="font-bold flex items-center gap-1">
                      <span>🛒 Gupta Kirana Bot</span>
                      {result.is_tatkal && (
                        <span className="bg-amber-500 text-slate-950 px-1.5 py-0.2 rounded text-[9px] font-bold animate-pulse">
                          ⚡ TATKAL (10 MINS)
                        </span>
                      )}
                    </span>
                    <span className="text-emerald-200 text-[10px] font-mono">#{result.note_id.slice(0, 8)}</span>
                  </div>

                  {/* Formatted WhatsApp Markdown Message */}
                  <pre className="text-xs font-sans whitespace-pre-wrap text-emerald-50 leading-relaxed bg-[#024a3c]/70 p-3 rounded-xl border border-emerald-400/20">
                    {result.whatsapp_auto_reply_text}
                  </pre>

                  {/* Dynamic UPI Payment Rail Card */}
                  <div className="bg-[#023e32] p-3 rounded-xl border border-emerald-400/30 flex items-center justify-between gap-3">
                    <div className="space-y-1">
                      <div className="text-[10px] font-mono text-emerald-300 uppercase">Dynamic UPI QR Code</div>
                      <div className="text-sm font-bold text-white">₹{result.cart_total_inr.toFixed(2)}</div>
                      <div className="text-[10px] text-emerald-200/80">Gupta Kirana Store • Verified Merchant</div>
                    </div>
                    <div className="w-16 h-16 bg-white p-1 rounded-lg flex items-center justify-center flex-shrink-0 shadow">
                      <QrCode className="w-14 h-14 text-slate-900" />
                    </div>
                  </div>

                  {/* Spoken Voice Confirmation Audio (Gnani Timbre TTS) */}
                  <div className="flex items-center justify-between gap-2 pt-1">
                    <button
                      onClick={() => playSyntheticTone(true)}
                      className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors"
                    >
                      {isPlayingReply ? <Pause className="w-3.5 h-3.5 fill-current" /> : <Play className="w-3.5 h-3.5 fill-current" />}
                      <span>{isPlayingReply ? "Playing Voice Note..." : "Listen Timbre Voice Reply"}</span>
                    </button>

                    <div className="flex items-center gap-2">
                      {onImportToLiveCart && (
                        <button
                          onClick={() => {
                            if (result?.transcript) {
                              onImportToLiveCart(result.transcript);
                              onClose();
                            }
                          }}
                          className="px-3 py-1.5 rounded-lg bg-teal-600/30 hover:bg-teal-600/50 text-teal-200 border border-teal-500/40 text-xs font-semibold flex items-center gap-1 transition-colors"
                        >
                          <ShoppingBag className="w-3.5 h-3.5 text-teal-300" />
                          <span>Import to Counter</span>
                        </button>
                      )}

                      <a
                        href={`https://api.whatsapp.com/send?phone=919820112345&text=${encodeURIComponent(result.whatsapp_auto_reply_text)}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-3 py-1.5 rounded-lg bg-slate-900/80 hover:bg-slate-900 text-emerald-300 text-xs font-semibold flex items-center gap-1 transition-colors"
                      >
                        <span>Share on WhatsApp</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                  </div>

                  <div className="text-right text-[10px] text-emerald-200/70 flex items-center justify-end gap-1">
                    <span>{result.received_timestamp}</span>
                    <CheckCheck className="w-3.5 h-3.5 text-sky-300" />
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
