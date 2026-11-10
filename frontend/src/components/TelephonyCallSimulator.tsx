import React, { useState, useEffect, useRef } from "react";
import { Phone, PhoneCall, PhoneOff, Volume2, VolumeX, User, Play, Pause, RotateCcw, Bot } from "lucide-react";

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
    description: "Tests intelligent voice substitution when Amul Butter is marked out of stock.",
    audioUrl: "/audio-samples/clip_4_dairy_snacks_telephony_fan_10db.wav"
  },
  {
    id: "call_bhasha_sudhaar",
    callerName: "Rajesh Kumar (राजेश • Live Correction)",
    callerPhone: "+91 98555-67890",
    tag: "Bhasha-Sudhaar Repair",
    utterance: "Bhaiya 5 kilo आशीर्वाद आटा, नहीं नहीं 5 नहीं 2 kilo कर दो, और Maggi मत भेजना कैंसिल कर दो।",
    description: "Tests real-time mid-utterance conversational repair and item cancellation."
  },
  {
    id: "call_bhav_pucho",
    callerName: "Pooja Sharma (पूजा • Rate Check)",
    callerPhone: "+91 98666-78901",
    tag: "Bhav Pucho Rate Check",
    utterance: "Bhaiya Basmati chawal aur Fortune oil ka kya bhav chal raha hai?",
    description: "Price discovery intent: returns spoken price quotes without adding to cart."
  },
  {
    id: "call_missed_call",
    callerName: "Sunita Devi (सुनीता देवी • Missed Call)",
    callerPhone: "+91 98444-56789",
    tag: "Missed Call -> Auto AI Callback",
    utterance: "हाँ गुप्ता जी, 2 packet ताज़ा दूध और एक किलो चीनी भेज दीजिए, बस इतना ही।",
    description: "Simulates missed-call ordering common in Bharat: AI automatically calls back to take order."
  }
];

interface TelephonyCallSimulatorProps {
  onProcessCallUtterance: (text: string, audioBlob?: Blob) => void;
  isLoading: boolean;
  activeClarification?: boolean;
  onClose: () => void;
  apiBaseUrl?: string;
  voiceAudioBase64?: string;
  voiceAudioFormat?: string;
  spokenReplyHi?: string;
  spokenReplyEn?: string;
}

export const TelephonyCallSimulator: React.FC<TelephonyCallSimulatorProps> = ({
  onProcessCallUtterance,
  isLoading,
  activeClarification,
  onClose,
  apiBaseUrl = "",
  voiceAudioBase64,
  voiceAudioFormat = "wav",
  spokenReplyHi,
  spokenReplyEn
}) => {
  const [callState, setCallState] = useState<"IDLE" | "RINGING" | "CONNECTED" | "ENDED">("RINGING");
  const [selectedPreset, setSelectedPreset] = useState<CallPreset>(CALL_PRESETS[0]);
  const [durationSec, setDurationSec] = useState<number>(0);
  const [simulatedTelephoneSpeaker, setSimulatedTelephoneSpeaker] = useState(true);
  const [isCallerAudioPlaying, setIsCallerAudioPlaying] = useState(false);
  const [isAssistantAudioPlaying, setIsAssistantAudioPlaying] = useState(false);
  const [ringMuted, setRingMuted] = useState(false);

  const timerRef = useRef<any>(null);
  const callerAudioRef = useRef<HTMLAudioElement | null>(null);
  const assistantAudioRef = useRef<HTMLAudioElement | null>(null);
  const ringAudioCtxRef = useRef<AudioContext | null>(null);
  const ringIntervalRef = useRef<any>(null);

  // Helper to resolve audio URL
  const resolveAudioUrl = (urlPath?: string) => {
    if (!urlPath) return "";
    if (urlPath.startsWith("http")) return urlPath;
    return `${apiBaseUrl}${urlPath}`;
  };

  // Play telephone ringing sound via Web Audio API
  const startRingtone = () => {
    if (ringMuted) return;
    try {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      ringAudioCtxRef.current = ctx;

      const pulseRing = () => {
        if (!ringAudioCtxRef.current || ringAudioCtxRef.current.state === "closed") return;
        const now = ctx.currentTime;
        const osc1 = ctx.createOscillator();
        const osc2 = ctx.createOscillator();
        const gain = ctx.createGain();

        osc1.type = "sine";
        osc2.type = "sine";
        osc1.frequency.value = 440;
        osc2.frequency.value = 480;

        gain.gain.setValueAtTime(0.04, now);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 1.6);

        osc1.connect(gain);
        osc2.connect(gain);
        gain.connect(ctx.destination);

        osc1.start(now);
        osc2.start(now);
        osc1.stop(now + 1.6);
        osc2.stop(now + 1.6);
      };

      pulseRing();
      ringIntervalRef.current = setInterval(pulseRing, 3500);
    } catch (e) {
      console.warn("Could not start telephone ringtone:", e);
    }
  };

  const stopRingtone = () => {
    if (ringIntervalRef.current) {
      clearInterval(ringIntervalRef.current);
      ringIntervalRef.current = null;
    }
    if (ringAudioCtxRef.current) {
      ringAudioCtxRef.current.close().catch(() => {});
      ringAudioCtxRef.current = null;
    }
  };

  // Stop all active audio elements
  const stopAllAudio = () => {
    stopRingtone();
    if (callerAudioRef.current) {
      callerAudioRef.current.pause();
      callerAudioRef.current.currentTime = 0;
      setIsCallerAudioPlaying(false);
    }
    if (assistantAudioRef.current) {
      assistantAudioRef.current.pause();
      assistantAudioRef.current.currentTime = 0;
      setIsAssistantAudioPlaying(false);
    }
  };

  // Ring tone control based on callState
  useEffect(() => {
    if (callState === "RINGING" && !ringMuted) {
      startRingtone();
    } else {
      stopRingtone();
    }
    return () => stopRingtone();
  }, [callState, ringMuted]);

  // Duration timer during connected call
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

  // Clean up on component unmount
  useEffect(() => {
    return () => {
      stopAllAudio();
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  // Update volume when speaker mode toggles
  useEffect(() => {
    const vol = simulatedTelephoneSpeaker ? 1.0 : 0.0;
    if (callerAudioRef.current) callerAudioRef.current.volume = vol;
    if (assistantAudioRef.current) assistantAudioRef.current.volume = vol;
  }, [simulatedTelephoneSpeaker]);

  // Play Caller Audio Clip
  const playCallerAudio = (preset: CallPreset) => {
    if (!preset.audioUrl) return;

    if (callerAudioRef.current) {
      callerAudioRef.current.pause();
      callerAudioRef.current.currentTime = 0;
    }

    const resolvedUrl = resolveAudioUrl(preset.audioUrl);
    const audio = new Audio(resolvedUrl);
    audio.volume = simulatedTelephoneSpeaker ? 1.0 : 0.0;
    callerAudioRef.current = audio;
    setIsCallerAudioPlaying(true);

    audio.onended = () => {
      setIsCallerAudioPlaying(false);
    };

    audio.onerror = (e) => {
      console.warn("Caller audio playback error:", e);
      setIsCallerAudioPlaying(false);
    };

    audio.play().catch((err) => {
      console.warn("Caller audio playback prevented by browser:", err);
      setIsCallerAudioPlaying(false);
    });
  };

  // Play Assistant Spoken Confirmation Audio
  const playAssistantAudio = (b64Audio?: string, format: string = "wav") => {
    const rawB64 = b64Audio || voiceAudioBase64;
    if (!rawB64) return;

    if (assistantAudioRef.current) {
      assistantAudioRef.current.pause();
      assistantAudioRef.current.currentTime = 0;
    }

    const mime = format === "mp3" ? "audio/mp3" : "audio/wav";
    const audioUrl = `data:${mime};base64,${rawB64}`;
    const audio = new Audio(audioUrl);
    audio.volume = simulatedTelephoneSpeaker ? 1.0 : 0.0;
    assistantAudioRef.current = audio;
    setIsAssistantAudioPlaying(true);

    audio.onended = () => {
      setIsAssistantAudioPlaying(false);
    };

    audio.onerror = (e) => {
      console.warn("Assistant voice audio error:", e);
      setIsAssistantAudioPlaying(false);
    };

    audio.play().catch((err) => {
      console.warn("Assistant audio playback prevented:", err);
      setIsAssistantAudioPlaying(false);
    });
  };

  // When call is accepted: connect call and immediately play caller's voice stream!
  const handleAcceptCall = () => {
    stopRingtone();
    setCallState("CONNECTED");
    playCallerAudio(selectedPreset);
    onProcessCallUtterance(selectedPreset.utterance);
  };

  // Automatically play assistant's response once order processing returns TTS audio
  useEffect(() => {
    if (callState === "CONNECTED" && voiceAudioBase64) {
      // If caller audio is currently speaking, wait for caller to finish first
      if (callerAudioRef.current && !callerAudioRef.current.paused && isCallerAudioPlaying) {
        callerAudioRef.current.onended = () => {
          setIsCallerAudioPlaying(false);
          // Natural conversational gap (400ms) before store assistant replies
          setTimeout(() => {
            playAssistantAudio(voiceAudioBase64, voiceAudioFormat);
          }, 450);
        };
      } else {
        // Caller has finished, reply immediately
        const timer = setTimeout(() => {
          playAssistantAudio(voiceAudioBase64, voiceAudioFormat);
        }, 300);
        return () => clearTimeout(timer);
      }
    }
  }, [voiceAudioBase64, callState]);

  const handleDeclineOrHangup = () => {
    stopAllAudio();
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
            <PhoneCall className={`w-4 h-4 ${callState === "RINGING" ? "animate-bounce" : ""}`} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              PSTN Telephony Incoming Call Simulator
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                Live 8 kHz Mobile Line
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-sky-500/20 text-sky-300 border border-sky-500/30">
                Full Voice Duplex
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Simulates live phone orders received at Gupta Kirana Store with caller & assistant audio
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Speaker Mute/Unmute Toggle */}
          <button
            onClick={() => setSimulatedTelephoneSpeaker((prev) => !prev)}
            className={`text-xs px-2.5 py-1 rounded-lg border flex items-center gap-1.5 transition-all ${
              simulatedTelephoneSpeaker
                ? "bg-emerald-500/15 border-emerald-500/40 text-emerald-300"
                : "bg-slate-800 border-slate-700 text-slate-400"
            }`}
            title="Toggle phone speaker audio"
          >
            {simulatedTelephoneSpeaker ? (
              <>
                <Volume2 className="w-3.5 h-3.5 text-emerald-400" />
                <span className="hidden sm:inline">Speaker ON</span>
              </>
            ) : (
              <>
                <VolumeX className="w-3.5 h-3.5 text-slate-400" />
                <span className="hidden sm:inline">Speaker Muted</span>
              </>
            )}
          </button>

          <button
            onClick={() => {
              stopAllAudio();
              onClose();
            }}
            className="text-xs text-slate-400 hover:text-white px-2.5 py-1 rounded bg-slate-800 border border-slate-700 transition-colors"
          >
            Exit Call Mode
          </button>
        </div>
      </div>

      {/* Preset Caller Selection */}
      <div className="mb-4">
        <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1.5">
          Select Simulated Caller Scenario:
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {CALL_PRESETS.map((preset) => (
            <button
              key={preset.id}
              onClick={() => {
                if (callState === "CONNECTED") {
                  stopAllAudio();
                }
                setSelectedPreset(preset);
                setCallState("RINGING");
              }}
              className={`p-2.5 rounded-lg text-left transition-all border ${
                selectedPreset.id === preset.id
                  ? "bg-emerald-950/40 border-emerald-500/60 text-white shadow-md shadow-emerald-950/50"
                  : "bg-slate-900/80 border-slate-800 text-slate-300 hover:border-slate-700"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white">{preset.callerName}</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-teal-300 font-mono">
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
            <div
              className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-white shadow-lg ${
                callState === "CONNECTED"
                  ? "bg-gradient-to-tr from-emerald-500 to-teal-500 shadow-emerald-500/20"
                  : callState === "RINGING"
                  ? "bg-emerald-600 animate-pulse"
                  : "bg-slate-800"
              }`}
            >
              <User className="w-6 h-6" />
            </div>

            <div>
              <div className="text-sm font-bold text-white flex items-center gap-2">
                {selectedPreset.callerName}
                {callState === "RINGING" && (
                  <span className="text-[10px] text-amber-400 font-mono animate-pulse font-normal flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping inline-block"></span>
                    Incoming Call Ringing...
                  </span>
                )}
                {callState === "CONNECTED" && (
                  <span className="text-[10px] text-emerald-400 font-mono font-normal flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block"></span>
                    Call Active • {formatTimer(durationSec)}
                  </span>
                )}
                {callState === "ENDED" && (
                  <span className="text-[10px] text-rose-400 font-mono font-normal">
                    Call Disconnected
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
              <div className="flex items-center gap-2 flex-wrap justify-end">
                {/* Audio Status Pill */}
                {isCallerAudioPlaying && (
                  <span className="text-xs text-emerald-300 font-medium flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/20 border border-emerald-500/40 animate-pulse">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
                    Caller Speaking (8 kHz PSTN)
                  </span>
                )}

                {isAssistantAudioPlaying && (
                  <span className="text-xs text-sky-300 font-medium flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-sky-500/20 border border-sky-500/40 animate-pulse">
                    <span className="w-2 h-2 rounded-full bg-sky-400 animate-ping"></span>
                    Assistant Replying (Timbre TTS)
                  </span>
                )}

                {isLoading && !isCallerAudioPlaying && !isAssistantAudioPlaying && (
                  <span className="text-xs text-teal-400 font-medium flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-teal-500/10 border border-teal-500/20">
                    <span className="w-2 h-2 rounded-full bg-teal-400 animate-ping"></span>
                    Processing Audio Stream...
                  </span>
                )}

                <button
                  onClick={handleDeclineOrHangup}
                  className="px-3.5 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold flex items-center gap-1.5 transition-all"
                >
                  <PhoneOff className="w-3.5 h-3.5" />
                  End Call (कॉल काटें)
                </button>
              </div>
            )}

            {(callState === "IDLE" || callState === "ENDED") && (
              <button
                onClick={() => setCallState("RINGING")}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold flex items-center gap-2 border border-slate-700 transition-all"
              >
                <PhoneCall className="w-4 h-4 text-emerald-400" />
                Simulate Another Incoming Call
              </button>
            )}
          </div>
        </div>

        {/* Live Audio Dialogue Transcript & Audio Player Bubbles */}
        {callState === "CONNECTED" && (
          <div className="mt-4 pt-3 border-t border-slate-800/80 space-y-3">
            {/* Caller Voice Bubble */}
            <div className="p-3 rounded-xl bg-slate-900 border border-emerald-500/30">
              <div className="text-[11px] text-slate-400 font-medium mb-1.5 flex items-center justify-between">
                <span className="flex items-center gap-1.5 text-emerald-300">
                  <User className="w-3.5 h-3.5" />
                  Caller Spoken Stream (8 kHz PSTN Codec):
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => playCallerAudio(selectedPreset)}
                    className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/40 text-emerald-200 flex items-center gap-1 transition-colors"
                    title="Replay caller voice"
                  >
                    {isCallerAudioPlaying ? (
                      <>
                        <Pause className="w-3 h-3 text-emerald-300" /> Playing Caller Voice
                      </>
                    ) : (
                      <>
                        <Play className="w-3 h-3 text-emerald-300" /> Replay Caller Voice
                      </>
                    )}
                  </button>
                  <span className="text-[10px] text-emerald-400 font-mono hidden sm:inline">
                    Prisma Auto-LID Transcribing
                  </span>
                </div>
              </div>
              <div className="text-white text-xs font-medium italic">
                "{selectedPreset.utterance}"
              </div>
            </div>

            {/* Store Assistant Audio Reply Bubble (When available) */}
            {(spokenReplyHi || voiceAudioBase64) && (
              <div className="p-3 rounded-xl bg-sky-950/40 border border-sky-500/30">
                <div className="text-[11px] text-slate-400 font-medium mb-1.5 flex items-center justify-between">
                  <span className="flex items-center gap-1.5 text-sky-300">
                    <Bot className="w-3.5 h-3.5" />
                    Gupta Kirana Spoken Response (Timbre TTS):
                  </span>
                  {voiceAudioBase64 && (
                    <button
                      onClick={() => playAssistantAudio(voiceAudioBase64, voiceAudioFormat)}
                      className="text-[10px] px-2 py-0.5 rounded bg-sky-500/20 hover:bg-sky-500/30 border border-sky-500/40 text-sky-200 flex items-center gap-1 transition-colors"
                      title="Replay store spoken readback"
                    >
                      {isAssistantAudioPlaying ? (
                        <>
                          <Pause className="w-3 h-3 text-sky-300" /> Playing Store Readback
                        </>
                      ) : (
                        <>
                          <Play className="w-3 h-3 text-sky-300" /> Replay Store Readback
                        </>
                      )}
                    </button>
                  )}
                </div>
                <div className="text-slate-200 text-xs font-medium italic">
                  "{spokenReplyHi || spokenReplyEn}"
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
