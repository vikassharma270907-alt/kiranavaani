import React, { useState, useEffect, useRef } from "react";
import { Phone, PhoneCall, PhoneOff, Volume2, User, Clock, CheckCircle2, AlertTriangle, ArrowRight, Sparkles } from "lucide-react";

export interface CallPreset {
  id: string;
  callerName: string;
  callerPhone: string;
  tag: string;
  utterance: string;
  description: string;
  audioUrl?: string;
  isAmbiguous?: boolean;
}

const CALL_PRESETS: CallPreset[] = [
  {
    id: "call_sharma_ji",
    callerName: "Sharma Ji (शर्मा जी • Regular)",
    callerPhone: "+91 98111-23456",
    tag: "Khata Credit Order",
    utterance: "Sharma ji ke khaate me likh lo bhaiya, do packet Maggi, ek kilo sugar aur aadha litre milk bhej dena, bas itna hi.",
    description: "Multi-item grocery replenishment booked directly to Customer Khata #42.",
    audioUrl: "/audio-samples/clip_1_brand_keyterms_telephony_traffic_5db.wav"
  },
  {
    id: "call_ambiguous_rice",
    callerName: "Verma Ji (वर्मा जी)",
    callerPhone: "+91 98222-34567",
    tag: "Ambiguity Clarification",
    utterance: "Gupta ji do kilo chawal aur ek packet Tata Salt bhej dena.",
    description: "Generic 'chawal' mention triggers active Basmati vs Sona Masoori clarification loop.",
    audioUrl: "/audio-samples/clip_2_ambiguous_rice_telephony_fan_20db.wav",
    isAmbiguous: true
  },
  {
    id: "call_kannada_bangalore",
    callerName: "Ramesh Gowda (Namma Bengaluru)",
    callerPhone: "+91 98333-45678",
    tag: "Kannada + Hinglish Auto-LID",
    utterance: "Anna ondu kilo godhi hittu, eradu packet Maggi matthe ardha litre milk kodi, aste.",
    description: "Kannada colloquial numerals (ondu=1, eradu=2, ardha=0.5) with completion cue 'aste'.",
    audioUrl: "/audio-samples/clip_5_kannada_hinglish_telephony_clean_20db.wav"
  },
  {
    id: "call_butter_stockout",
    callerName: "Anjali Devi (सुनीता/अंजलि)",
    callerPhone: "+91 98444-56789",
    tag: "Out-of-Stock Substitution",
    utterance: "Bhaiya ek Amul butter aur ek kilo Basmati rice bhej dena.",
    description: "Tests intelligent voice substitution when Amul Butter is marked out of stock."
  }
];

interface TelephonyCallSimulatorProps {
  onProcessCallUtterance: (text: string, audioBlob?: Blob) => void;
  isLoading: boolean;
  activeClarification?: boolean;
  onClose: () => void;
}

export const TelephonyCallSimulator: React.FC<TelephonyCallSimulatorProps> = ({
  onProcessCallUtterance,
  isLoading,
  activeClarification,
  onClose
}) => {
  const [callState, setCallState] = useState<"IDLE" | "RINGING" | "CONNECTED" | "ENDED">("RINGING");
  const [selectedPreset, setSelectedPreset] = useState<CallPreset>(CALL_PRESETS[0]);
  const [durationSec, setDurationSec] = useState<number>(0);
  const [simulatedTelephoneSpeaker, setSimulatedTelephoneSpeaker] = useState(true);
  const timerRef = useRef<any>(null);

  useEffect(() => {
    if (callState === "CONNECTED") {
      setDurationSec(0);
      timerRef.current = setInterval(() => {
        setDurationSec((prev) => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [callState]);

  const handleAcceptCall = () => {
    setCallState("CONNECTED");
    // Trigger order processing with selected preset utterance
    onProcessCallUtterance(selectedPreset.utterance);
  };

  const handleDeclineOrHangup = () => {
    setCallState("ENDED");
    setTimeout(() => {
      setCallState("IDLE");
    }, 1500);
  };

  const formatTimer = (sec: number) => {
    const mins = Math.floor(sec / 60);
    const s = sec % 60;
    return `${mins.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <div className="bg-gradient-to-b from-slate-900 to-slate-950 border-2 border-emerald-500/40 rounded-2xl p-5 shadow-2xl relative overflow-hidden">
      {/* Top Banner / Call Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
            <PhoneCall className="w-4 h-4 animate-bounce" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              PSTN Telephony Incoming Call Simulator
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                Live 8 kHz Mobile Line
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Simulates a live phone order received at Gupta Kirana Store
            </p>
          </div>
        </div>

        <button
          onClick={onClose}
          className="text-xs text-slate-400 hover:text-white px-2 py-1 rounded bg-slate-800 border border-slate-700"
        >
          Exit Call Mode
        </button>
      </div>

      {/* Preset Caller Selection (Before or during call) */}
      <div className="mb-4">
        <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1.5">
          Select Simulated Caller Scenario:
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {CALL_PRESETS.map((preset) => (
            <button
              key={preset.id}
              onClick={() => {
                setSelectedPreset(preset);
                if (callState === "IDLE" || callState === "ENDED") {
                  setCallState("RINGING");
                }
              }}
              className={`p-2.5 rounded-lg text-left transition-all border ${
                selectedPreset.id === preset.id
                  ? "bg-emerald-950/40 border-emerald-500/60 text-white"
                  : "bg-slate-900/80 border-slate-800 text-slate-300 hover:border-slate-700"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white">{preset.callerName}</span>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-teal-300">
                  {preset.tag}
                </span>
              </div>
              <div className="text-[11px] text-slate-400 mt-1 line-clamp-1 italic">
                "{preset.utterance}"
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Mobile Telephony Call Window */}
      <div className="bg-slate-950 rounded-xl border border-slate-800 p-4 relative overflow-hidden">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          {/* Caller Identity */}
          <div className="flex items-center gap-3.5">
            <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-white shadow-lg ${
              callState === "CONNECTED"
                ? "bg-gradient-to-tr from-emerald-500 to-teal-500 shadow-emerald-500/20"
                : "bg-slate-800 animate-pulse"
            }`}>
              <User className="w-6 h-6" />
            </div>

            <div>
              <div className="text-sm font-bold text-white flex items-center gap-2">
                {selectedPreset.callerName}
                {callState === "RINGING" && (
                  <span className="text-[10px] text-amber-400 font-mono animate-pulse font-normal">
                    (Incoming Call Ringing...)
                  </span>
                )}
                {callState === "CONNECTED" && (
                  <span className="text-[10px] text-emerald-400 font-mono font-normal">
                    (Call Active • {formatTimer(durationSec)})
                  </span>
                )}
              </div>
              <div className="text-xs text-slate-400 font-mono">
                {selectedPreset.callerPhone} • <span className="text-teal-400">ITU-T G.711 μ-Law (8 kHz)</span>
              </div>
            </div>
          </div>

          {/* Call Action Controls */}
          <div className="flex items-center gap-3">
            {callState === "RINGING" && (
              <>
                <button
                  onClick={handleDeclineOrHangup}
                  className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold flex items-center gap-2 shadow-lg shadow-rose-600/30 transition-all"
                >
                  <PhoneOff className="w-4 h-4" />
                  Decline
                </button>

                <button
                  onClick={handleAcceptCall}
                  className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold flex items-center gap-2 shadow-lg shadow-emerald-600/30 transition-all animate-bounce"
                >
                  <Phone className="w-4 h-4" />
                  Accept Call (उत्तर दें)
                </button>
              </>
            )}

            {callState === "CONNECTED" && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-emerald-400 font-medium flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
                  Processing Audio Stream
                </span>

                <button
                  onClick={handleDeclineOrHangup}
                  className="px-3.5 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold flex items-center gap-1.5"
                >
                  <PhoneOff className="w-3.5 h-3.5" />
                  End Call (कॉल काटें)
                </button>
              </div>
            )}

            {(callState === "IDLE" || callState === "ENDED") && (
              <button
                onClick={() => setCallState("RINGING")}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold flex items-center gap-2 border border-slate-700"
              >
                <PhoneCall className="w-4 h-4 text-emerald-400" />
                Simulate Another Incoming Call
              </button>
            )}
          </div>
        </div>

        {/* Live Audio Dialogue Transcript Bubble during Call */}
        {callState === "CONNECTED" && (
          <div className="mt-3 pt-3 border-t border-slate-800/80">
            <div className="text-[11px] text-slate-400 font-medium mb-1 flex items-center justify-between">
              <span>Caller Spoken Stream (8 kHz PSTN Codec):</span>
              <span className="text-[10px] text-emerald-400 font-mono">Prisma v3.0 Auto-LID Transcribing...</span>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-900 border border-emerald-500/30 text-white text-xs font-medium italic">
              "{selectedPreset.utterance}"
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

