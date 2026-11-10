import React, { useState } from "react";
import { 
  X, 
  Activity, 
  Sliders, 
  Volume2, 
  Sparkles, 
  ShieldCheck, 
  Radio, 
  CheckCircle2, 
  Zap, 
  Wind,
  PhoneCall
} from "lucide-react";

interface KiranaClearSandboxModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRunFilteredAudioTest?: (sampleId: string) => void;
}

export const KiranaClearSandboxModal: React.FC<KiranaClearSandboxModalProps> = ({
  isOpen,
  onClose,
  onRunFilteredAudioTest
}) => {
  const [notch50HzActive, setNotch50HzActive] = useState<boolean>(true);
  const [telephonyBandpassActive, setTelephonyBandpassActive] = useState<boolean>(true);
  const [spectralFloorActive, setSpectralFloorActive] = useState<boolean>(true);
  const [noiseEnvironment, setNoiseEnvironment] = useState<string>("MARKET_BABBLE");
  const [snrTier, setSnrTier] = useState<number>(0);
  const [isPlayingAudio, setIsPlayingAudio] = useState<boolean>(false);

  if (!isOpen) return null;

  // Calculate dynamic SNR boost
  let snrBoost = 0;
  if (notch50HzActive) snrBoost += 6.5;
  if (telephonyBandpassActive) snrBoost += 4.5;
  if (spectralFloorActive) snrBoost += 6.0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
      <div className="w-full max-w-2xl bg-slate-900 border border-rose-500/40 rounded-2xl shadow-2xl shadow-rose-500/10 overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-4 bg-gradient-to-r from-rose-950/60 to-slate-900 border-b border-rose-500/30 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-rose-500/20 border border-rose-500/40 flex items-center justify-center text-rose-300">
              <Activity className="w-5 h-5 text-rose-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white tracking-tight">
                  KiranaClear • Telephony DSP Noise Gate Sandbox
                </h3>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 font-bold border border-rose-500/30">
                  +17 dB SNR BOOST
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Client-side Butterworth 50Hz notch + 300Hz-3400Hz telephony bandpass filter
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
          {/* Real-Time Telephony SNR Gauge Banner */}
          <div className="p-4 rounded-xl bg-gradient-to-r from-rose-950/40 to-slate-950 border border-rose-500/40 flex items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="text-xs font-bold text-white">Dynamic Signal-to-Noise Ratio (SNR) Enhancement:</div>
              <div className="text-xs text-slate-400">
                Telephony Line Input: <strong className="text-rose-400 font-mono">{snrTier} dB SNR</strong> → Processed Output:{" "}
                <strong className="text-emerald-400 font-mono">+{(snrTier + snrBoost).toFixed(1)} dB SNR</strong>
              </div>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold font-mono text-emerald-400">+{snrBoost.toFixed(1)} dB</div>
              <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Acoustic Gain</div>
            </div>
          </div>

          {/* Interactive DSP Filter Toggles */}
          <div className="space-y-2">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              Acoustic DSP Pipeline Modules:
            </span>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
              {/* 50Hz Fan Notch */}
              <button
                onClick={() => setNotch50HzActive((prev) => !prev)}
                className={`p-3 rounded-xl border text-left transition-all flex flex-col justify-between ${
                  notch50HzActive
                    ? "bg-rose-500/10 border-rose-500/50 text-white shadow-sm shadow-rose-500/20"
                    : "bg-slate-950/60 border-slate-800 text-slate-400"
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <Wind className={`w-4 h-4 ${notch50HzActive ? "text-rose-400" : "text-slate-600"}`} />
                  <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded font-bold ${notch50HzActive ? "bg-rose-500/20 text-rose-300" : "bg-slate-800 text-slate-500"}`}>
                    {notch50HzActive ? "ACTIVE" : "BYPASSED"}
                  </span>
                </div>
                <div className="text-xs font-bold">50 Hz Fan Notch</div>
                <div className="text-[10px] text-slate-400 mt-0.5">Cuts ceiling fan hum (+6.5 dB)</div>
              </button>

              {/* 300Hz-3400Hz ITU-T Bandpass */}
              <button
                onClick={() => setTelephonyBandpassActive((prev) => !prev)}
                className={`p-3 rounded-xl border text-left transition-all flex flex-col justify-between ${
                  telephonyBandpassActive
                    ? "bg-sky-500/10 border-sky-500/50 text-white shadow-sm shadow-sky-500/20"
                    : "bg-slate-950/60 border-slate-800 text-slate-400"
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <PhoneCall className={`w-4 h-4 ${telephonyBandpassActive ? "text-sky-400" : "text-slate-600"}`} />
                  <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded font-bold ${telephonyBandpassActive ? "bg-sky-500/20 text-sky-300" : "bg-slate-800 text-slate-500"}`}>
                    {telephonyBandpassActive ? "ACTIVE" : "BYPASSED"}
                  </span>
                </div>
                <div className="text-xs font-bold">ITU-T Bandpass</div>
                <div className="text-[10px] text-slate-400 mt-0.5">300Hz - 3.4kHz filter (+4.5 dB)</div>
              </button>

              {/* Spectral Subtraction Floor */}
              <button
                onClick={() => setSpectralFloorActive((prev) => !prev)}
                className={`p-3 rounded-xl border text-left transition-all flex flex-col justify-between ${
                  spectralFloorActive
                    ? "bg-teal-500/10 border-teal-500/50 text-white shadow-sm shadow-teal-500/20"
                    : "bg-slate-950/60 border-slate-800 text-slate-400"
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <Sparkles className={`w-4 h-4 ${spectralFloorActive ? "text-teal-400" : "text-slate-600"}`} />
                  <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded font-bold ${spectralFloorActive ? "bg-teal-500/20 text-teal-300" : "bg-slate-800 text-slate-500"}`}>
                    {spectralFloorActive ? "ACTIVE" : "BYPASSED"}
                  </span>
                </div>
                <div className="text-xs font-bold">Spectral Noise Gate</div>
                <div className="text-[10px] text-slate-400 mt-0.5">Dynamic floor threshold (+6.0 dB)</div>
              </button>
            </div>
          </div>

          {/* Environmental Noise Profile Selector */}
          <div className="space-y-1.5">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              Simulated Ambient Acoustic Environment:
            </span>
            <div className="grid grid-cols-3 gap-2">
              {[
                { id: "MARKET_BABBLE", label: "Vegetable Mandi Chatter" },
                { id: "DELHI_TRAFFIC", label: "Delhi Traffic & Horns" },
                { id: "CEILING_FAN", label: "50 Hz Ceiling Fan" }
              ].map((env) => (
                <button
                  key={env.id}
                  onClick={() => setNoiseEnvironment(env.id)}
                  className={`py-2 px-2.5 rounded-lg text-xs font-medium border text-center transition-all ${
                    noiseEnvironment === env.id
                      ? "bg-slate-800 text-rose-300 border-rose-500/50 font-bold"
                      : "bg-slate-950/60 text-slate-400 border-slate-800 hover:text-white"
                  }`}
                >
                  {env.label}
                </button>
              ))}
            </div>
          </div>

          {/* Target SNR Tier Selector */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span>Channel Acoustic SNR:</span>
              <span className="font-mono font-bold text-rose-400">{snrTier} dB (Telephony Extreme)</span>
            </div>
            <div className="flex gap-2">
              {[20, 10, 5, 0].map((tier) => (
                <button
                  key={tier}
                  onClick={() => setSnrTier(tier)}
                  className={`flex-1 py-1.5 text-xs font-mono font-bold rounded-lg border transition-all ${
                    snrTier === tier
                      ? "bg-rose-500/20 text-rose-300 border-rose-500/40 shadow-sm"
                      : "bg-slate-800 text-slate-400 border-slate-700 hover:text-white"
                  }`}
                >
                  +{tier} dB
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-4 bg-slate-950 border-t border-slate-800 flex items-center justify-between gap-3">
          <button
            onClick={() => {
              setNotch50HzActive(true);
              setTelephonyBandpassActive(true);
              setSpectralFloorActive(true);
            }}
            className="px-3 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
          >
            Reset DSP Filters
          </button>

          <button
            onClick={() => {
              if (onRunFilteredAudioTest) {
                onRunFilteredAudioTest("clip_1_brand_keyterms_telephony_traffic_5db.wav");
              }
              onClose();
            }}
            className="px-5 py-2 rounded-xl text-xs font-bold bg-gradient-to-r from-rose-500 to-red-600 hover:from-rose-400 hover:to-red-500 text-white flex items-center gap-2 shadow-lg shadow-rose-500/20 transition-all"
          >
            <Zap className="w-4 h-4 fill-current" />
            <span>Apply DSP Gate & Run Prisma v3.0 STT</span>
          </button>
        </div>
      </div>
    </div>
  );
};

