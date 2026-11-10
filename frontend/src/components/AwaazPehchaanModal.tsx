import React, { useState, useEffect } from "react";
import { 
  ShieldCheck, 
  ShieldAlert, 
  X, 
  Activity, 
  Volume2, 
  User, 
  AlertTriangle, 
  Fingerprint,
  Radio,
  Zap,
  Cpu,
  RefreshCw
} from "lucide-react";

export interface VoiceprintResponse {
  verified: boolean;
  customer_id: string;
  customer_name: string;
  match_score: number;
  confidence_tier: string;
  voiceprint_hash: string;
  fundamental_freq_f0_hz: number;
  formant_dispersion_hz: number;
  spectral_centroid_hz: number;
  jitter_percent: number;
  shimmer_db: number;
  auth_badge_text: string;
  auth_message_hi: string;
  auth_message_en: string;
  khata_debit_permitted: boolean;
  voice_audio_base64?: string;
  voice_audio_format?: string;
}

export interface LivenessResponse {
  is_live: boolean;
  liveness_score: number;
  attack_detected: string | null;
  spectral_flux: number;
  jitter_ppq5: number;
  loudspeaker_resonance_peak_db: number;
  analysis_text_hi: string;
  analysis_text_en: string;
  action_permitted: boolean;
}

interface AwaazPehchaanModalProps {
  isOpen: boolean;
  onClose: () => void;
  customerId?: string;
  customerName?: string;
  apiBaseUrl: string;
  onVerificationComplete?: (response: VoiceprintResponse) => void;
}

export const AwaazPehchaanModal: React.FC<AwaazPehchaanModalProps> = ({
  isOpen,
  onClose,
  customerId = "CUST-001",
  customerName = "Sharma Ji (शर्मा जी)",
  apiBaseUrl,
  onVerificationComplete
}) => {
  const [activeTab, setActiveTab] = useState<"voiceprint" | "liveness">("voiceprint");
  const [isImposterMode, setIsImposterMode] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [authResult, setAuthResult] = useState<VoiceprintResponse | null>(null);
  const [isPlayingAudio, setIsPlayingAudio] = useState<boolean>(false);
  const audioRef = React.useRef<HTMLAudioElement | null>(null);

  // Armour360 Liveness State
  const [livenessMode, setLivenessMode] = useState<"authentic" | "replay" | "clone">("authentic");
  const [livenessResult, setLivenessResult] = useState<LivenessResponse | null>(null);
  const [isLivenessLoading, setIsLivenessLoading] = useState<boolean>(false);

  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (isOpen) {
      if (activeTab === "voiceprint") {
        verifyVoiceprint(isImposterMode);
      } else {
        checkLiveness(livenessMode);
      }
    }
  }, [isOpen, activeTab, isImposterMode, livenessMode]);

  const verifyVoiceprint = async (imposter: boolean) => {
    setIsLoading(true);
    try {
      const res = await fetch(`${apiBaseUrl}/khata/verify-voiceprint`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer_id: customerId,
          caller_phone: "+91 98111-23456",
          test_imposter_mode: imposter
        })
      });
      if (res.ok) {
        const data: VoiceprintResponse = await res.json();
        setAuthResult(data);
        if (onVerificationComplete) {
          onVerificationComplete(data);
        }
      }
    } catch (e) {
      console.warn("Voiceprint verification network error:", e);
    } finally {
      setIsLoading(false);
    }
  };

  const checkLiveness = async (mode: "authentic" | "replay" | "clone") => {
    setIsLivenessLoading(true);
    try {
      const attackType = mode === "replay" ? "replay_attack" : mode === "clone" ? "ai_cloned_voice" : null;
      const res = await fetch(`${apiBaseUrl}/khata/liveness-check`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer_id: customerId,
          simulate_attack_type: attackType
        })
      });
      if (res.ok) {
        const data: LivenessResponse = await res.json();
        setLivenessResult(data);
      }
    } catch (e) {
      console.warn("Liveness check network error:", e);
    } finally {
      setIsLivenessLoading(false);
    }
  };

  const handlePlayVoiceNote = () => {
    if (!authResult?.voice_audio_base64) return;
    if (isPlayingAudio && audioRef.current) {
      audioRef.current.pause();
      setIsPlayingAudio(false);
      return;
    }
    if (audioRef.current) {
      audioRef.current.pause();
    }
    const audio = new Audio(`data:audio/${authResult.voice_audio_format || "wav"};base64,${authResult.voice_audio_base64}`);
    audioRef.current = audio;
    setIsPlayingAudio(true);
    audio.onended = () => setIsPlayingAudio(false);
    audio.onerror = () => setIsPlayingAudio(false);
    audio.play();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-2xl bg-slate-900 border border-teal-500/30 rounded-2xl shadow-2xl flex flex-col max-h-[92vh] overflow-hidden">
        {/* Header Bar */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-gradient-to-r from-teal-950/40 via-slate-900 to-slate-950">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-teal-500/20 border border-teal-500/40 flex items-center justify-center text-teal-400 shadow-lg shadow-teal-500/10">
              <Fingerprint className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-white tracking-wide">
                  Awaaz Pehchaan <span className="text-teal-400 font-hindi font-normal text-sm">(आवाज़ पहचान)</span>
                </h3>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-teal-500/20 text-teal-300 border border-teal-500/30 font-mono font-semibold">
                  GNANI ARMOUR360 INSPIRED
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Acoustic Voice Biometrics & Customer Authentication for Kirana Khata Credit Protection
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

        {/* Tab Switcher */}
        <div className="flex border-b border-slate-800 bg-slate-950/60 px-6 pt-2 gap-2">
          <button
            onClick={() => setActiveTab("voiceprint")}
            className={`pb-2.5 px-3 text-xs font-semibold border-b-2 flex items-center gap-1.5 transition-all ${
              activeTab === "voiceprint"
                ? "border-teal-400 text-teal-300 font-bold"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <Fingerprint className="w-3.5 h-3.5" />
            <span>Voiceprint Biometrics (बायोमेट्रिक पहचान)</span>
          </button>
          <button
            onClick={() => setActiveTab("liveness")}
            className={`pb-2.5 px-3 text-xs font-semibold border-b-2 flex items-center gap-1.5 transition-all ${
              activeTab === "liveness"
                ? "border-amber-400 text-amber-300 font-bold"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <Radio className="w-3.5 h-3.5 text-amber-400" />
            <span>Armour360 Anti-Spoofing & Liveness (एंटी-स्पूफिंग गेट)</span>
            <span className="text-[9px] bg-amber-500/20 text-amber-300 px-1.5 py-0.2 rounded font-mono font-bold">
              NEW
            </span>
          </button>
        </div>

        {/* Body Content */}
        <div className="p-6 space-y-5 overflow-y-auto">
          {activeTab === "voiceprint" ? (
            <>
              {/* Target Customer Card & Mode Switch */}
              <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-xl bg-slate-950 border border-slate-800">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300">
                    <User className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="text-sm font-bold text-white">{customerName}</div>
                    <div className="text-xs text-slate-400 font-mono">
                      Enrolled Khata ID: <strong>{customerId}</strong> • +91 98111-23456
                    </div>
                  </div>
                </div>

                {/* Test Imposter Simulation Toggle */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setIsImposterMode((prev) => !prev)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1.5 border ${
                      isImposterMode
                        ? "bg-rose-500/20 text-rose-300 border-rose-500/40"
                        : "bg-slate-800 text-slate-400 border-slate-700 hover:text-white"
                    }`}
                  >
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span>{isImposterMode ? "⚠️ Imposter Mode: ACTIVE" : "Test Imposter Call"}</span>
                  </button>
                </div>
              </div>

              {/* Biometric Verification Banner */}
              {authResult && (
                <div
                  className={`p-4 rounded-xl border space-y-3 transition-all ${
                    authResult.verified
                      ? "bg-emerald-950/20 border-emerald-500/40 shadow-lg shadow-emerald-500/5"
                      : "bg-rose-950/20 border-rose-500/40 shadow-lg shadow-rose-500/5"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {authResult.verified ? (
                        <ShieldCheck className="w-5 h-5 text-emerald-400" />
                      ) : (
                        <ShieldAlert className="w-5 h-5 text-rose-400 animate-pulse" />
                      )}
                      <span
                        className={`text-sm font-bold tracking-wide ${
                          authResult.verified ? "text-emerald-300" : "text-rose-300"
                        }`}
                      >
                        {authResult.auth_badge_text}
                      </span>
                    </div>

                    <div className="text-right">
                      <span className="text-xs text-slate-400">Biometric Match: </span>
                      <span
                        className={`font-mono font-bold text-sm ${
                          authResult.verified ? "text-emerald-400" : "text-rose-400"
                        }`}
                      >
                        {(authResult.match_score * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>

                  {/* Message */}
                  <p className="text-xs text-slate-300 font-hindi leading-relaxed">
                    {authResult.auth_message_hi}
                  </p>

                  {/* Spoken voice feedback */}
                  {authResult.voice_audio_base64 && (
                    <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between gap-3">
                      <span className="text-[11px] text-slate-400">
                        Timbre Spoken Voice Response:
                      </span>
                      <button
                        onClick={handlePlayVoiceNote}
                        className="px-3 py-1 rounded-md bg-teal-500/10 hover:bg-teal-500/20 text-teal-300 text-xs font-semibold border border-teal-500/30 flex items-center gap-1.5 transition"
                      >
                        <Volume2 className="w-3.5 h-3.5 text-teal-400" />
                        <span>{isPlayingAudio ? "Pause Audio" : "Listen to Timbre Voice"}</span>
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Acoustic Timbre Physics Matrix */}
              {authResult && (
                <div className="space-y-2">
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-wider px-1 flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5 text-sky-400" />
                    Live Acoustic Feature Extraction & Harmonic Physics
                  </span>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                    <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                      <div className="text-[10px] text-slate-400 uppercase font-semibold">Fundamental Pitch (F0)</div>
                      <div className="text-base font-mono font-bold text-white">
                        {authResult.fundamental_freq_f0_hz} <span className="text-xs text-slate-400">Hz</span>
                      </div>
                      <div className="text-[10px] text-slate-500">Target Range: 120-145 Hz</div>
                    </div>

                    <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                      <div className="text-[10px] text-slate-400 uppercase font-semibold">Formant Dispersion</div>
                      <div className="text-base font-mono font-bold text-sky-400">
                        {authResult.formant_dispersion_hz} <span className="text-xs text-slate-400">Hz</span>
                      </div>
                      <div className="text-[10px] text-slate-500">Vocal Tract Geometry</div>
                    </div>

                    <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                      <div className="text-[10px] text-slate-400 uppercase font-semibold">Spectral Centroid</div>
                      <div className="text-base font-mono font-bold text-teal-400">
                        {authResult.spectral_centroid_hz} <span className="text-xs text-slate-400">Hz</span>
                      </div>
                      <div className="text-[10px] text-slate-500">Timbre Brightness</div>
                    </div>

                    <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                      <div className="text-[10px] text-slate-400 uppercase font-semibold">Pitch Jitter</div>
                      <div className="text-base font-mono font-bold text-amber-400">
                        {authResult.jitter_percent} <span className="text-xs text-slate-400">%</span>
                      </div>
                      <div className="text-[10px] text-slate-500">Micro-Perturbation</div>
                    </div>
                  </div>

                  {/* Encrypted Voiceprint Fingerprint Hash */}
                  <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-[11px] font-mono text-slate-400 flex items-center justify-between gap-2 overflow-x-auto">
                    <span className="text-slate-500 font-semibold whitespace-nowrap">Voiceprint Template:</span>
                    <span className="text-teal-400 truncate">{authResult.voiceprint_hash}</span>
                  </div>
                </div>
              )}
            </>
          ) : (
            /* Tab 2: Armour360 Liveness & Anti-Spoofing */
            <div className="space-y-5 animate-fade-in">
              {/* Threat Simulation Mode Selectors */}
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                    <Radio className="w-3.5 h-3.5 text-amber-400" />
                    Armour360 Acoustic Liveness & Anti-Spoofing Simulator
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono">Gnani Armour360 Core Tech</span>
                </div>
                
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                  <button
                    onClick={() => setLivenessMode("authentic")}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      livenessMode === "authentic"
                        ? "bg-emerald-950/40 border-emerald-500 text-white shadow-md shadow-emerald-500/10"
                        : "bg-slate-900 border-slate-800 text-slate-400 hover:text-white"
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <ShieldCheck className="w-4 h-4 text-emerald-400" />
                      <span className="text-xs font-bold">1. Genuine Live Voice</span>
                    </div>
                    <p className="text-[10px] text-slate-400 leading-tight">
                      Authentic human vocal cords with organic physiological pitch jitter (PPQ5).
                    </p>
                  </button>

                  <button
                    onClick={() => setLivenessMode("replay")}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      livenessMode === "replay"
                        ? "bg-rose-950/40 border-rose-500 text-white shadow-md shadow-rose-500/10"
                        : "bg-slate-900 border-slate-800 text-slate-400 hover:text-white"
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <AlertTriangle className="w-4 h-4 text-rose-400" />
                      <span className="text-xs font-bold">2. Replay Attack</span>
                    </div>
                    <p className="text-[10px] text-slate-400 leading-tight">
                      Recorded WhatsApp voice note replayed through smartphone loudspeaker (+5.2 dB at 3.2 kHz).
                    </p>
                  </button>

                  <button
                    onClick={() => setLivenessMode("clone")}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      livenessMode === "clone"
                        ? "bg-purple-950/40 border-purple-500 text-white shadow-md shadow-purple-500/10"
                        : "bg-slate-900 border-slate-800 text-slate-400 hover:text-white"
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <Cpu className="w-4 h-4 text-purple-400" />
                      <span className="text-xs font-bold">3. AI Voice Clone</span>
                    </div>
                    <p className="text-[10px] text-slate-400 leading-tight">
                      TTS Deepfake audio with unnaturally low jitter flatline (PPQ5 &lt; 0.2%).
                    </p>
                  </button>
                </div>
              </div>

              {/* Liveness Result Telemetry Banner */}
              {livenessResult && (
                <div
                  className={`p-4 rounded-xl border space-y-3 transition-all ${
                    livenessResult.is_live
                      ? "bg-emerald-950/20 border-emerald-500/40 shadow-lg shadow-emerald-500/5"
                      : "bg-rose-950/25 border-rose-500/50 shadow-lg shadow-rose-500/10"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {livenessResult.is_live ? (
                        <ShieldCheck className="w-5 h-5 text-emerald-400" />
                      ) : (
                        <ShieldAlert className="w-5 h-5 text-rose-400 animate-pulse" />
                      )}
                      <span
                        className={`text-sm font-bold tracking-wide ${
                          livenessResult.is_live ? "text-emerald-300" : "text-rose-300"
                        }`}
                      >
                        {livenessResult.is_live
                          ? "✅ ACOUSTIC LIVENESS CONFIRMED (GENUINE HUMAN)"
                          : "🚨 SPOOFING / REPLAY ATTACK BLOCKED"}
                      </span>
                    </div>

                    <div className="text-right">
                      <span className="text-xs text-slate-400">Liveness Confidence: </span>
                      <span
                        className={`font-mono font-bold text-sm ${
                          livenessResult.is_live ? "text-emerald-400" : "text-rose-400"
                        }`}
                      >
                        {(livenessResult.liveness_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>

                  {/* Hindi & English Analysis */}
                  <div className="space-y-1">
                    <p className="text-xs text-slate-200 font-hindi leading-relaxed">
                      {livenessResult.analysis_text_hi}
                    </p>
                    <p className="text-[11px] text-slate-400 italic">
                      {livenessResult.analysis_text_en}
                    </p>
                  </div>

                  {/* Khata Credit Protection Action */}
                  <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
                    <span className="text-slate-400">Kirana Khata Debit Authorization:</span>
                    <span
                      className={`font-bold px-2 py-0.5 rounded text-[11px] font-mono ${
                        livenessResult.action_permitted
                          ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                          : "bg-rose-500/20 text-rose-300 border border-rose-500/30 animate-pulse"
                      }`}
                    >
                      {livenessResult.action_permitted ? "✅ KHATA DEBIT AUTHORIZED" : "🛑 KHATA DEBIT BLOCKED"}
                    </span>
                  </div>
                </div>
              )}

              {/* Real-time Acoustic Waveform & Transducer Matrix */}
              {livenessResult && (
                <div className="space-y-2">
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-wider px-1 flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5 text-amber-400" />
                    Armour360 Transducer & Biometric Telemetry Matrix
                  </span>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                    {/* Spectral Flux */}
                    <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                      <div className="text-[10px] text-slate-400 uppercase font-semibold">Spectral Dynamic Flux</div>
                      <div className={`text-base font-mono font-bold ${
                        livenessResult.spectral_flux >= 0.40 ? "text-emerald-400" : "text-rose-400"
                      }`}>
                        {livenessResult.spectral_flux.toFixed(2)}
                      </div>
                      <div className="text-[10px] text-slate-500">Live Speech: &ge; 0.40 (Natural variability)</div>
                    </div>

                    {/* Jitter PPQ5 */}
                    <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                      <div className="text-[10px] text-slate-400 uppercase font-semibold">Pitch Micro-Jitter (PPQ5)</div>
                      <div className={`text-base font-mono font-bold ${
                        livenessResult.jitter_ppq5 >= 0.50 ? "text-emerald-400" : "text-rose-400"
                      }`}>
                        {livenessResult.jitter_ppq5.toFixed(2)} <span className="text-xs text-slate-400">%</span>
                      </div>
                      <div className="text-[10px] text-slate-500">Synthetic Voice: &lt; 0.20% (AI Flatline)</div>
                    </div>

                    {/* Loudspeaker Resonance */}
                    <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                      <div className="text-[10px] text-slate-400 uppercase font-semibold">Secondary Speaker Peak</div>
                      <div className={`text-base font-mono font-bold ${
                        livenessResult.loudspeaker_resonance_peak_db <= 1.0 ? "text-emerald-400" : "text-rose-400"
                      }`}>
                        +{livenessResult.loudspeaker_resonance_peak_db.toFixed(1)} <span className="text-xs text-slate-400">dB</span>
                      </div>
                      <div className="text-[10px] text-slate-500">Replay Signature: +3.5 to +5.2 dB at 3.2 kHz</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Educational Note */}
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-[11px] text-slate-400 space-y-1">
            <strong className="text-slate-200">Gnani.ai Product Alignment:</strong> Inspired by Gnani's enterprise <em>Armour360</em> Voice Biometrics & Anti-Spoofing engine. Protects uncollateralized Kirana Khata ledger credit against WhatsApp audio replay fraud and modern voice cloning deepfakes.
          </div>
        </div>

        {/* Footer Bar */}
        <div className="px-6 py-3.5 border-t border-slate-800 bg-slate-950 flex items-center justify-between gap-3 text-xs text-slate-500">
          <span>Enterprise Biometrics Mode • Armour360 Acoustic Alignment</span>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold transition"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
