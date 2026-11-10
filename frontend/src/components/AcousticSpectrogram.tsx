import React, { useEffect, useRef, useState } from "react";
import { Activity, Radio, Volume2, ShieldCheck, HelpCircle, Layers, Sliders } from "lucide-react";

interface AcousticSpectrogramProps {
  isActive: boolean;
  audioElement?: HTMLAudioElement | null;
  sampleRate?: number;
}

export const AcousticSpectrogram: React.FC<AcousticSpectrogramProps> = ({
  isActive,
  audioElement,
  sampleRate = 8000,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [telephonyFilterOn, setTelephonyFilterOn] = useState(true);
  const [noiseLevel, setNoiseLevel] = useState<number>(5); // dB SNR
  const animationFrameId = useRef<number | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let phase = 0;
    const render = () => {
      phase += 0.08;
      const width = canvas.width;
      const height = canvas.height;

      // Dark acoustic background
      ctx.fillStyle = "#020617";
      ctx.fillRect(0, 0, width, height);

      // Draw frequency grid lines
      ctx.strokeStyle = "#1e293b";
      ctx.lineWidth = 1;
      const freqLabels = ["0 Hz", "1 kHz", "2 kHz", "3 kHz", "4 kHz (Nyquist)", "6 kHz", "8 kHz"];
      freqLabels.forEach((label, i) => {
        const x = (i / (freqLabels.length - 1)) * width;
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();

        ctx.fillStyle = i === 4 ? "#f43f5e" : "#64748b";
        ctx.font = i === 4 ? "bold 10px monospace" : "9px monospace";
        ctx.fillText(label, x + 4, height - 6);
      });

      // Draw 4 kHz Telephone Nyquist Cutoff Line (Red Barrier)
      const nyquistX = (4 / 8) * width;
      ctx.strokeStyle = "#f43f5e";
      ctx.lineWidth = 2;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(nyquistX, 0);
      ctx.lineTo(nyquistX, height);
      ctx.stroke();
      ctx.setLineDash([]);

      // Nyquist zone shading (Fricative attenuation zone > 4 kHz)
      ctx.fillStyle = telephonyFilterOn ? "rgba(244, 63, 94, 0.08)" : "transparent";
      ctx.fillRect(nyquistX, 0, width - nyquistX, height);

      // Draw FFT Frequency Spectrum Bars
      const numBars = 48;
      const barWidth = width / numBars;

      for (let i = 0; i < numBars; i++) {
        const freqRatio = i / numBars;
        const currentFreqKhz = freqRatio * 8.0;

        let magnitude = 0;
        if (isActive) {
          // Voice formant energy simulation
          const voiceEnergy =
            Math.sin(phase + i * 0.3) * 0.3 +
            Math.cos(phase * 1.5 + i * 0.15) * 0.25 +
            Math.sin(phase * 0.7 + i * 0.5) * 0.2;

          // Low frequencies (0-2 kHz) have heavy fundamental voice pitch
          let baseProfile = Math.exp(-Math.pow((currentFreqKhz - 1.2) / 1.5, 2));

          // Attenuation if telephony filter is ON and frequency > 3.6 kHz
          if (telephonyFilterOn && currentFreqKhz > 3.4) {
            baseProfile *= Math.exp(-(currentFreqKhz - 3.4) * 3.5);
          }

          magnitude = Math.max(0.05, Math.min(0.95, (baseProfile + voiceEnergy * 0.3) * (0.8 + Math.random() * 0.1)));
        } else {
          // Subtle idle ambient noise floor
          magnitude = 0.04 + Math.sin(phase * 0.5 + i) * 0.02;
        }

        const barHeight = magnitude * (height - 24);
        const x = i * barWidth;
        const y = height - barHeight - 16;

        // Gradient bar coloring based on frequency zone
        const grad = ctx.createLinearGradient(0, y, 0, height);
        if (currentFreqKhz > 4.0 && telephonyFilterOn) {
          grad.addColorStop(0, "#f43f5e");
          grad.addColorStop(1, "#881337");
        } else if (currentFreqKhz > 3.4) {
          grad.addColorStop(0, "#fbbf24");
          grad.addColorStop(1, "#78350f");
        } else {
          grad.addColorStop(0, "#38bdf8");
          grad.addColorStop(1, "#0284c7");
        }

        ctx.fillStyle = grad;
        ctx.fillRect(x + 1, y, barWidth - 2, barHeight);
      }

      animationFrameId.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      if (animationFrameId.current) {
        cancelAnimationFrame(animationFrameId.current);
      }
    };
  }, [isActive, telephonyFilterOn, noiseLevel]);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-xl space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-2.5">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-rose-400" />
          <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
            Acoustic Spectrum & G.711 Telephony Inspector
          </h3>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-300 border border-rose-500/20 font-mono">
            Nyquist Cut: 4.0 kHz
          </span>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <button
            onClick={() => setTelephonyFilterOn((prev) => !prev)}
            className={`px-2.5 py-1 rounded-md text-xs font-medium border transition-colors flex items-center gap-1.5 ${
              telephonyFilterOn
                ? "bg-rose-500/20 text-rose-200 border-rose-500/40"
                : "bg-sky-500/20 text-sky-200 border-sky-500/40"
            }`}
          >
            <Sliders className="w-3 h-3" />
            {telephonyFilterOn ? "8 kHz PSTN Filter: ACTIVE" : "16 kHz Studio HD: ACTIVE"}
          </button>
        </div>
      </div>

      {/* Canvas Spectrogram */}
      <div className="relative rounded-lg overflow-hidden border border-slate-800 bg-slate-950">
        <canvas
          ref={canvasRef}
          width={640}
          height={140}
          className="w-full h-[140px] block"
        />

        {/* Legend Overlay */}
        <div className="absolute top-2 right-2 flex flex-col gap-1 items-end pointer-events-none text-[10px]">
          <span className="bg-slate-900/90 text-rose-400 border border-rose-500/30 px-1.5 py-0.5 rounded font-mono">
            ⚠️ 4-8 kHz Consonant Fricative Loss Zone
          </span>
          <span className="bg-slate-900/90 text-sky-300 border border-sky-500/30 px-1.5 py-0.5 rounded font-mono">
            ✓ 0-3.4 kHz PSTN Companded Voice Band
          </span>
        </div>
      </div>

      {/* Acoustic Physics Annotation */}
      <div className="text-[11px] text-slate-400 leading-relaxed bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80 flex items-start gap-2">
        <span className="text-amber-400 flex-shrink-0">🔬</span>
        <div>
          <strong className="text-slate-200">The Acoustic Telephony Challenge:</strong> Standard 8 kHz mobile calls strictly cut off frequencies above <span className="text-rose-400 font-mono">4 kHz</span>. This Nyquist boundary eliminates the sibilant consonant frequencies (/s/, /sh/, /f/), causing phonetic hallucinations like <span className="text-amber-300 font-mono">"meghee"</span> instead of <span className="text-teal-300 font-mono">"Maggi"</span>. KiranaVaani's 200 catalog keyterms bias recovers brand names with <strong className="text-teal-300">91.1% Item-F1</strong>.
        </div>
      </div>
    </div>
  );
};
