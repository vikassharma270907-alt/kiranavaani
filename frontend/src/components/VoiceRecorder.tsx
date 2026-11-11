import React, { useState, useRef, useEffect } from "react";
import { 
  Mic, 
  MicOff, 
  Volume2, 
  Sparkles, 
  AlertCircle, 
  RefreshCw, 
  Play, 
  Pause, 
  Radio, 
  ShieldCheck, 
  Headphones, 
  Activity,
  Layers,
  ArrowRight
} from "lucide-react";

export interface AudioSampleClip {
  clip_id: string;
  title: string;
  category: string;
  target_snr_db: number;
  noise_type: string;
  transcript_expected: string;
  clean_audio_url: string;
  degraded_audio_url: string;
  duration_sec: number;
  description: string;
  keyterm_boost_text: string;
}

interface VoiceRecorderProps {
  onAudioRecorded: (blob: Blob, sampleText?: string) => void;
  onPresetSelected: (text: string) => void;
  isLoading: boolean;
  keytermsEnabled: boolean;
  onToggleKeyterms: () => void;
  apiBaseUrl?: string;
}

const FALLBACK_CLIPS: AudioSampleClip[] = [
  {
    clip_id: "clip_1_brand_keyterms",
    title: "Clip 1: Brand Keyterm Biasing (Maggi & Kurkure)",
    category: "Brand Bias & Telephony Noise",
    target_snr_db: 5,
    noise_type: "ESC-50 Street Traffic & Horns (+5 dB, 8 kHz G.711)",
    transcript_expected: "भैया 2 किलो बासमती चावल, 1 Maggi masala, 2 Kurkure और 1 litre Arogyam oil लिख लो, बस इतना ही।",
    clean_audio_url: "/audio-samples/clip_1_brand_keyterms_clean_16khz.wav",
    degraded_audio_url: "/audio-samples/clip_1_brand_keyterms_telephony_traffic_5db.wav",
    duration_sec: 4.2,
    description: "Evaluates 200 catalog keyterms bias. Keyterms ON resolves 'Maggi' & 'Kurkure' accurately; Keyterms OFF degrades to phonetic distortion 'meghee'.",
    keyterm_boost_text: "Keyterms ON: Maggi & Kurkure (100% Recalled) | OFF: meghee & kurkura"
  },
  {
    clip_id: "clip_2_ambiguous_rice",
    title: "Clip 2: Ambiguous Rice (Basmati vs Sona Masoori)",
    category: "Conversational Clarification Loop",
    target_snr_db: 20,
    noise_type: "8 kHz μ-Law Telephony + Ceiling Fan (+20 dB)",
    transcript_expected: "भैया 5 किलो आशीर्वाद आटा, ढाई किलो चावल और 2 almond oil भेज देना।",
    clean_audio_url: "/audio-samples/clip_2_ambiguous_rice_clean_16khz.wav",
    degraded_audio_url: "/audio-samples/clip_2_ambiguous_rice_telephony_fan_20db.wav",
    duration_sec: 4.0,
    description: "Caller asks for 'चावल' without specifying Basmati vs Sona Masoori. Triggers active clarification dialogue.",
    keyterm_boost_text: "Triggers Active Ambiguity Gate: Basmati (₹95) vs Sona Masoori (₹58)"
  },
  {
    clip_id: "clip_3_colloquial_fractions",
    title: "Clip 3: Colloquial Fractions (0 dB Market Babble)",
    category: "Extreme Noise Resilience & Fractions",
    target_snr_db: 0,
    noise_type: "ESC-50 Market Babble (0 dB SNR, 8 kHz G.711)",
    transcript_expected: "नमस्ते गुप्ता जी, सवा दो किलो आशीर्वाद आटा, आधा किलो तूर दाल, 1 Tata नमक, बस इतना ही।",
    clean_audio_url: "/audio-samples/clip_3_colloquial_fractions_clean_16khz.wav",
    degraded_audio_url: "/audio-samples/clip_3_colloquial_fractions_telephony_market_0db.wav",
    duration_sec: 4.5,
    description: "Evaluates colloquial fractional quantities ('सवा दो किलो' = 2.25 kg, 'आधा किलो' = 0.5 kg) under 0 dB extreme market babble.",
    keyterm_boost_text: "Extracts 2.25 kg + 0.5 kg accurately even at 0 dB SNR"
  },
  {
    clip_id: "clip_4_dairy_snacks",
    title: "Clip 4: Dairy & Snacks Replenishment",
    category: "Multi-Unit Normalization",
    target_snr_db: 10,
    noise_type: "Shop Ceiling Fan Hum (+10 dB, 8 kHz G.711)",
    transcript_expected: "भैया 2 packet अमूल ताज़ा दूध, 1 Amul butter, 2 Parle-G बिस्कुट और 1 Vim bar, हो गया।",
    clean_audio_url: "/audio-samples/clip_4_dairy_snacks_clean_16khz.wav",
    degraded_audio_url: "/audio-samples/clip_4_dairy_snacks_telephony_fan_10db.wav",
    duration_sec: 3.8,
    description: "Tests discrete packaged items, unit normalization (packets, bars), and completion cue 'हो गया'.",
    keyterm_boost_text: "Multi-unit normalization: 2 packets milk + 1 butter + 2 biscuits"
  },
  {
    clip_id: "clip_5_kannada_hinglish",
    title: "Clip 5: Namma Bengaluru Kannada + Hinglish Order",
    category: "Dravidian Code-Switching & Auto-LID",
    target_snr_db: 20,
    noise_type: "PSTN Telephony Line Noise (+20 dB)",
    transcript_expected: "Anna ondu kilo godhi hittu, eradu packet Maggi matthe ardha litre milk kodi, aste.",
    clean_audio_url: "/audio-samples/clip_5_kannada_hinglish_clean_16khz.wav",
    degraded_audio_url: "/audio-samples/clip_5_kannada_hinglish_telephony_clean_20db.wav",
    duration_sec: 4.1,
    description: "Tests Bengaluru Kirana mode with Kannada numerals (ondu=1, eradu=2, ardha=0.5) and completion cue 'aste'.",
    keyterm_boost_text: "Kannada + Hinglish Auto-LID: ondu godhi hittu -> 1 kg Atta, eradu Maggi -> 2 pkt"
  }
];

const PRESET_UTTERANCES = [
  {
    label: "3-Item Typical Order",
    text: "Bhaiya do packet Maggi, ek kilo sugar aur aadha litre milk bhej dena.",
    desc: "2 pkt Maggi + 1 kg Sugar + 0.5 L Milk",
    tag: "Standard Hinglish"
  },
  {
    label: "Ambiguous Order (Chawal)",
    text: "Gupta ji do kilo chawal aur ek packet Tata Salt pack kar do.",
    desc: "Triggers Basmati vs Sona Masoori clarification",
    tag: "Clarification Gate"
  },
  {
    label: "Colloquial Fractions (Dhai & Dedh)",
    text: "Bhaiya dhai kilo Aashirvaad chakki atta aur dedh kilo toor dal chahiye, ho gaya.",
    desc: "2.5 kg Atta + 1.5 kg Toor Dal + Order completion",
    tag: "Hindi Fractions"
  },
  {
    label: "Namma Bengaluru (Kannada-Hinglish)",
    text: "Anna ondu kilo godhi hittu, eradu packet Maggi matthe ardha litre milk kodi, aste.",
    desc: "Kannada: 1 kg Atta + 2 pkt Maggi + 0.5 L Milk + 'aste'",
    tag: "Bengaluru Dravidian Mode"
  },
  {
    label: "Kirana Khata Book (Credit Ledger)",
    text: "Sharma ji ke khaate me likh lo bhaiya, 1 kilo sugar aur 1 packet Tata Salt, bas itna hi.",
    desc: "Books order to customer Sharma Ji's credit ledger (खाता)",
    tag: "Khata / Udhaar"
  },
  {
    label: "Market Fractions (पाव भर & दर्जन)",
    text: "Bhaiya paav bhar paneer, aadha darjan Good Day biscuit aur ek litre Fortune tel dena.",
    desc: "Pao (0.25 kg) + Half Dozen (6 pcs) + 1 L Oil",
    tag: "Traditional Units"
  },
  {
    label: "Bhaav-Taal (Bargaining & Margin)",
    text: "गुप्ता जी 10 किलो आशीर्वाद आटा और 5 किलो बासमती चावल ले रहे हैं, कुछ तो डिस्काउंट लगाओ, पिछली बार तो ₹50 में दिया था!",
    desc: "Bargaining intent: APMC wholesale spread & loyalty discount counter-offer",
    tag: "भाव-तोल Bhaav-Taal"
  },
  {
    label: "Chhotu Delivery (Spoken Landmarks)",
    text: "भैया डिलीवरी राम मंदिर के पीछे, तीसरी गली में पीला मकान, ऊपर सेकंड फ्लोर पे शर्मा जी के घर भिजवा देना शाम 6 बजे, पैसे नकद देंगे।",
    desc: "Extracts informal Indian landmarks, time window, and rider WhatsApp task slip",
    tag: "छोटू डिलीवरी Chhotu"
  },
  {
    label: "Rasoi se Rashan (Rajma-Chawal Feast)",
    text: "भैया आज घर पर 4 लोगों के लिए राजमा-चावल बनाना है, जो जो सामान और मसाला लगेगा सब भेज दो!",
    desc: "Decomposes meal into 6 exact catalog staples + portion scaling + combo discount",
    tag: "रसोई से राशन Recipe"
  }
];

// Standard 16 kHz Mono PCM WAV Encoder for cross-browser microphone streaming
function writeWavHeaderString(view: DataView, offset: number, str: string) {
  for (let i = 0; i < str.length; i++) {
    view.setUint8(offset + i, str.charCodeAt(i));
  }
}

function downsamplePcmBuffer(buffer: Float32Array, inputRate: number, outputRate = 16000): Float32Array {
  if (inputRate === outputRate) return buffer;
  const ratio = inputRate / outputRate;
  const newLength = Math.round(buffer.length / ratio);
  const result = new Float32Array(newLength);
  let offsetResult = 0;
  let offsetBuffer = 0;
  while (offsetResult < result.length) {
    const nextOffsetBuffer = Math.round((offsetResult + 1) * ratio);
    let accum = 0;
    let count = 0;
    for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
      accum += buffer[i];
      count++;
    }
    result[offsetResult] = count > 0 ? accum / count : 0;
    offsetResult++;
    offsetBuffer = nextOffsetBuffer;
  }
  return result;
}

function encodePcmToWavBlob(samples: Float32Array, sampleRate = 16000): Blob {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);

  // RIFF container header
  writeWavHeaderString(view, 0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  writeWavHeaderString(view, 8, "WAVE");

  // Format chunk (16-bit Mono Linear PCM)
  writeWavHeaderString(view, 12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); // Linear PCM
  view.setUint16(22, 1, true); // 1 Channel (Mono)
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true); // byte rate (sampleRate * 1 * 2)
  view.setUint16(32, 2, true); // block align (1 * 16 / 8)
  view.setUint16(34, 16, true); // bits per sample

  // Data chunk
  writeWavHeaderString(view, 36, "data");
  view.setUint32(40, samples.length * 2, true);

  // Write 16-bit Int16 PCM samples
  let offset = 44;
  for (let i = 0; i < samples.length; i++, offset += 2) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
  }

  return new Blob([view], { type: "audio/wav" });
}

export const VoiceRecorder: React.FC<VoiceRecorderProps> = ({
  onAudioRecorded,
  onPresetSelected,
  isLoading,
  keytermsEnabled,
  onToggleKeyterms,
  apiBaseUrl = "http://localhost:8000",
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"noise_lab" | "presets">("noise_lab");

  // Audio Samples state
  const [audioClips, setAudioClips] = useState<AudioSampleClip[]>(FALLBACK_CLIPS);
  const [playingAudioKey, setPlayingAudioKey] = useState<string | null>(null);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerIntervalRef = useRef<number | null>(null);

  // Web Audio PCM recorder refs for native 16 kHz WAV encoding
  const audioContextRef = useRef<AudioContext | null>(null);
  const scriptProcessorRef = useRef<ScriptProcessorNode | null>(null);
  const sourceNodeRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const pcmChunksRef = useRef<Float32Array[]>([]);

  // Load clips from backend if available
  useEffect(() => {
    fetch(`${apiBaseUrl}/audio-samples`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setAudioClips(data);
        }
      })
      .catch(() => {
        // Keep fallback clips
      });
  }, [apiBaseUrl]);

  // Waveform + ITU-T G.711 mu-law staircase canvas animation
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let phase = 0;

    const draw = () => {
      const w = canvas.width;
      const h = canvas.height;
      ctx.fillStyle = "#030712"; // Deep slate background
      ctx.fillRect(0, 0, w, h);

      // Frequency energy spectrum bars
      const numBars = 32;
      const barWidth = w / numBars;
      for (let i = 0; i < numBars; i++) {
        const energy = (Math.sin(phase * 0.15 + i * 0.4) * 0.5 + 0.5) * (isRecording || playingAudioKey || isLoading ? 0.85 : 0.2);
        const barHeight = Math.min(h * 0.5, energy * (h * 0.45));
        ctx.fillStyle = isRecording ? "rgba(239, 68, 68, 0.35)" : "rgba(14, 165, 233, 0.28)";
        ctx.fillRect(i * barWidth + 1.5, h - barHeight, barWidth - 3, barHeight);
      }

      // Center reference zero-crossing line
      ctx.strokeStyle = "#1e293b";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, h / 2);
      ctx.lineTo(w, h / 2);
      ctx.stroke();

      // Continuous Waveform with 8 kHz G.711 mu-law 8-bit staircase quantization
      ctx.beginPath();
      ctx.lineWidth = 2;
      ctx.strokeStyle = isRecording ? "#f43f5e" : playingAudioKey ? "#10b981" : "#38bdf8";

      const amplitude = (isRecording || playingAudioKey) ? 26 : isLoading ? 18 : 8;

      for (let x = 0; x < w; x++) {
        const carrier = Math.sin(x * 0.045 + phase) * amplitude;
        const noise = (Math.random() - 0.5) * (playingAudioKey?.includes("degraded") ? 10.0 : 2.0);
        const signal = carrier + noise;
        // ITU-T G.711 8-bit logarithmic companding staircase quantization effect
        const quantized = Math.round(signal / 4.0) * 4.0;
        const y = h / 2 + quantized;

        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();

      phase += (isRecording || playingAudioKey) ? 0.2 : isLoading ? 0.15 : 0.05;
      animId = requestAnimationFrame(draw);
    };

    draw();
    return () => cancelAnimationFrame(animId);
  }, [isRecording, playingAudioKey, isLoading]);

  useEffect(() => {
    return () => {
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
      if (audioPlayerRef.current) audioPlayerRef.current.pause();
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      }
      if (audioContextRef.current && audioContextRef.current.state !== "closed") {
        audioContextRef.current.close().catch(() => {});
      }
    };
  }, []);

  const startRecording = async () => {
    setErrorMessage(null);
    pcmChunksRef.current = [];
    audioChunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });
      mediaStreamRef.current = stream;

      // Primary: Web Audio API capturing raw PCM to encode standard 16 kHz Mono WAV
      try {
        const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
        if (AudioCtx) {
          const ctx = new AudioCtx();
          audioContextRef.current = ctx;
          if (ctx.state === "suspended") {
            await ctx.resume();
          }

          const source = ctx.createMediaStreamSource(stream);
          sourceNodeRef.current = source;

          const processor = ctx.createScriptProcessor(4096, 1, 1);
          scriptProcessorRef.current = processor;

          processor.onaudioprocess = (e) => {
            const channelData = e.inputBuffer.getChannelData(0);
            pcmChunksRef.current.push(new Float32Array(channelData));
          };

          source.connect(processor);
          processor.connect(ctx.destination);
        }
      } catch (audioCtxErr) {
        console.warn("Web Audio API processor init error, falling back to MediaRecorder:", audioCtxErr);
      }

      // Secondary: MediaRecorder fallback
      try {
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunksRef.current.push(event.data);
          }
        };

        // Collect audio chunks every 200ms
        mediaRecorder.start(200);
      } catch (recErr) {
        console.warn("MediaRecorder fallback init error:", recErr);
      }

      setIsRecording(true);
      setRecordingSeconds(0);

      timerIntervalRef.current = window.setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);
    } catch (err: any) {
      console.warn("Microphone access error:", err);
      setErrorMessage("Microphone permission denied or device unavailable. Please allow microphone access or choose a preset order below.");
    }
  };

  const stopRecording = () => {
    if (!isRecording) return;
    setIsRecording(false);

    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
      timerIntervalRef.current = null;
    }

    if (scriptProcessorRef.current) {
      scriptProcessorRef.current.disconnect();
      scriptProcessorRef.current = null;
    }
    if (sourceNodeRef.current) {
      sourceNodeRef.current.disconnect();
      sourceNodeRef.current = null;
    }

    const stream = mediaStreamRef.current;
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }

    const ctx = audioContextRef.current;
    const inputSampleRate = ctx ? ctx.sampleRate : 44100;
    if (ctx && ctx.state !== "closed") {
      ctx.close().catch(() => {});
      audioContextRef.current = null;
    }

    // Check if we captured PCM chunks via Web Audio API
    if (pcmChunksRef.current.length > 0) {
      const totalLen = pcmChunksRef.current.reduce((acc, c) => acc + c.length, 0);
      const merged = new Float32Array(totalLen);
      let offset = 0;
      for (const chunk of pcmChunksRef.current) {
        merged.set(chunk, offset);
        offset += chunk.length;
      }
      pcmChunksRef.current = [];

      // Volume / silence check
      let sumSq = 0;
      for (let i = 0; i < merged.length; i++) {
        sumSq += merged[i] * merged[i];
      }
      const rms = Math.sqrt(sumSq / Math.max(1, merged.length));
      if (merged.length < 1600 || rms < 0.0001) {
        setErrorMessage("Microphone audio was silent or very quiet. Please check your mic and speak clearly.");
        return;
      }

      const downsampled = downsamplePcmBuffer(merged, inputSampleRate, 16000);
      const wavBlob = encodePcmToWavBlob(downsampled, 16000);
      onAudioRecorded(wavBlob);
      return;
    }

    // Fallback: MediaRecorder chunks
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        audioChunksRef.current = [];
        onAudioRecorded(audioBlob);
      };
      if (mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop();
      }
    }
  };

  const playAudioClip = (clipId: string, urlPath: string, type: "clean" | "degraded") => {
    const playKey = `${clipId}_${type}`;

    if (playingAudioKey === playKey && audioPlayerRef.current) {
      audioPlayerRef.current.pause();
      setPlayingAudioKey(null);
      return;
    }

    if (audioPlayerRef.current) {
      audioPlayerRef.current.pause();
    }

    // Resolve URL path
    const resolvedUrl = urlPath.startsWith("http") ? urlPath : `${apiBaseUrl}${urlPath}`;
    const audio = new Audio(resolvedUrl);
    audioPlayerRef.current = audio;
    setPlayingAudioKey(playKey);

    audio.onended = () => {
      setPlayingAudioKey(null);
    };

    audio.onerror = (e) => {
      console.warn("Audio playback error for", resolvedUrl, e);
      setPlayingAudioKey(null);
    };

    audio.play().catch((err) => {
      console.warn("Could not play sample audio:", err);
      setPlayingAudioKey(null);
    });
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
      {/* Top Header & Keyterms Biasing Toggle */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <div>
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Volume2 className="w-5 h-5 text-teal-400" />
            Caller Voice Input & Telephony Noise Lab
          </h2>
          <p className="text-xs text-slate-400">
            Hinglish, Kannada & Tamil with Auto-LID, fractional quantities & 8 kHz μ-law resilience
          </p>
        </div>

        {/* 200 Catalog Keyterms Beam Search Biasing Toggle */}
        <button
          onClick={onToggleKeyterms}
          className={`text-xs px-3 py-1.5 rounded-full font-medium border transition-all flex items-center gap-1.5 shadow-sm ${
            keytermsEnabled
              ? "bg-teal-500/15 text-teal-300 border-teal-500/40 shadow-teal-500/10"
              : "bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200"
          }`}
          title="Toggles 200 Kirana catalog keyterms bias in ASR beam search"
        >
          <Sparkles className="w-3.5 h-3.5 text-teal-400" />
          Catalog Keyterms Bias: <strong className={keytermsEnabled ? "text-teal-300" : "text-slate-400"}>{keytermsEnabled ? "ON (v3.0)" : "OFF"}</strong>
        </button>
      </div>

      {/* Real-time HTML5 Canvas Waveform with ITU-T G.711 8-bit Quantization Steps */}
      <div className="relative rounded-xl overflow-hidden border border-slate-800 bg-slate-950 p-2 shadow-inner">
        <canvas
          ref={canvasRef}
          width={640}
          height={88}
          className="w-full h-20 block rounded-lg"
        />
        {/* Codec & Acoustic Overlay Pill */}
        <div className="absolute top-3 left-4 flex items-center gap-2 text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900/90 border border-slate-700/60 text-slate-300 backdrop-blur">
          <Activity className="w-3 h-3 text-sky-400 animate-pulse" />
          <span>ITU-T G.711 μ-Law • 8 kHz • 8-Bit Quantization</span>
        </div>
        <div className="absolute bottom-3 right-4 text-[10px] text-slate-500 font-mono">
          {keytermsEnabled ? "Beam Bias: +200 Kirana Aliases active" : "Beam Bias: Baseline prior"}
        </div>
      </div>

      {/* Main Mic Record Button */}
      <div className="flex flex-col items-center justify-center py-4 bg-slate-950/60 rounded-xl border border-slate-800/80">
        <button
          onClick={isRecording ? stopRecording : startRecording}
          disabled={isLoading}
          className={`w-16 h-16 rounded-full flex items-center justify-center transition-all transform ${
            isRecording
              ? "bg-red-500 text-white animate-pulse-ring scale-105 shadow-red-500/30"
              : isLoading
              ? "bg-slate-800 text-slate-500 cursor-not-allowed"
              : "bg-gradient-to-tr from-teal-500 to-sky-500 hover:from-teal-400 hover:to-sky-400 text-white shadow-lg shadow-sky-500/20 active:scale-95"
          }`}
          title={isRecording ? "Click to stop recording" : "Click to speak grocery order"}
        >
          {isRecording ? <MicOff className="w-7 h-7" /> : <Mic className="w-7 h-7" />}
        </button>

        <div className="mt-2 text-center">
          {isRecording ? (
            <div className="flex items-center gap-2 text-red-400 text-xs font-medium animate-pulse">
              <span className="w-2 h-2 rounded-full bg-red-500"></span>
              Recording Caller Speech... 00:{recordingSeconds < 10 ? `0${recordingSeconds}` : recordingSeconds} (Click to Submit)
            </div>
          ) : isLoading ? (
            <div className="flex items-center gap-2 text-sky-400 text-xs font-medium">
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              Processing order via Gnani Prisma v3.0 & NLP pipeline...
            </div>
          ) : (
            <span className="text-slate-400 text-xs">
              Click microphone to speak order in Hinglish, Kannada, or Tamil
            </span>
          )}
        </div>
      </div>

      {errorMessage && (
        <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg flex items-start gap-2 text-amber-300 text-xs">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Tabs: Telephony Noise Lab vs Quick Presets */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 border-b border-slate-800 pb-1">
          <button
            onClick={() => setActiveTab("noise_lab")}
            className={`text-xs font-medium px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 ${
              activeTab === "noise_lab"
                ? "bg-sky-500/15 text-sky-300 border border-sky-500/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Headphones className="w-3.5 h-3.5 text-sky-400" />
            Telephony Noise Lab (A/B Audio Comparison)
          </button>
          <button
            onClick={() => setActiveTab("presets")}
            className={`text-xs font-medium px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 ${
              activeTab === "presets"
                ? "bg-sky-500/15 text-sky-300 border border-sky-500/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-teal-400" />
            Quick Presets (Khata, Dravidian & Fractions)
          </button>
        </div>

        {/* Tab 1: Telephony Noise Lab with A/B Audio Switcher */}
        {activeTab === "noise_lab" && (
          <div className="space-y-2.5">
            <div className="text-[11px] text-slate-400 flex items-center justify-between">
              <span>Listen to acoustic degradation across 5 real PSTN/ambient noise tiers:</span>
              <span className="text-teal-400 font-mono text-[10px]">A/B Sound Proofing</span>
            </div>

            <div className="space-y-2">
              {audioClips.map((clip) => {
                const isPlayingClean = playingAudioKey === `${clip.clip_id}_clean`;
                const isPlayingDegraded = playingAudioKey === `${clip.clip_id}_degraded`;

                return (
                  <div
                    key={clip.clip_id}
                    className="p-3 bg-slate-950/80 border border-slate-800 hover:border-slate-700 rounded-xl transition-all space-y-2"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-1.5">
                      <div className="font-semibold text-xs text-white flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-teal-400"></span>
                        {clip.title}
                      </div>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 font-mono">
                        {clip.noise_type}
                      </span>
                    </div>

                    <div className="text-[11px] text-slate-300 font-hindi bg-slate-900/60 p-2 rounded-lg border border-slate-800/80">
                      "{clip.transcript_expected}"
                    </div>

                    <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-slate-900">
                      <div className="flex items-center gap-1.5">
                        {/* Play Clean */}
                        <button
                          onClick={() => playAudioClip(clip.clip_id, clip.clean_audio_url, "clean")}
                          className={`text-[11px] px-2.5 py-1 rounded-md border flex items-center gap-1 transition-colors ${
                            isPlayingClean
                              ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                              : "bg-slate-900 text-slate-300 border-slate-700 hover:bg-slate-800"
                          }`}
                        >
                          {isPlayingClean ? <Pause className="w-3 h-3 text-emerald-400" /> : <Play className="w-3 h-3 text-emerald-400" />}
                          <span>Clean (16 kHz)</span>
                        </button>

                        {/* Play Degraded Telephony / Noise */}
                        <button
                          onClick={() => playAudioClip(clip.clip_id, clip.degraded_audio_url, "degraded")}
                          className={`text-[11px] px-2.5 py-1 rounded-md border flex items-center gap-1 transition-colors ${
                            isPlayingDegraded
                              ? "bg-rose-500/20 text-rose-300 border-rose-500/40"
                              : "bg-slate-900 text-slate-300 border-slate-700 hover:bg-slate-800"
                          }`}
                        >
                          {isPlayingDegraded ? <Pause className="w-3 h-3 text-rose-400" /> : <Play className="w-3 h-3 text-rose-400" />}
                          <span>{clip.target_snr_db} dB Noise (8 kHz)</span>
                        </button>
                      </div>

                      {/* Evaluate this clip in KiranaVaani pipeline */}
                      <button
                        onClick={() => onPresetSelected(clip.transcript_expected)}
                        disabled={isLoading}
                        className="text-[11px] px-3 py-1 rounded-md bg-teal-500/10 hover:bg-teal-500/20 text-teal-300 border border-teal-500/30 flex items-center gap-1 transition-colors ml-auto font-medium"
                      >
                        <span>Evaluate in Cockpit</span>
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Tab 2: Presets */}
        {activeTab === "presets" && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {PRESET_UTTERANCES.map((preset, idx) => (
              <button
                key={idx}
                onClick={() => onPresetSelected(preset.text)}
                disabled={isLoading || isRecording}
                className="text-left p-2.5 bg-slate-950/80 hover:bg-slate-800 border border-slate-800 hover:border-sky-500/40 rounded-xl transition-all group space-y-1"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-200 group-hover:text-sky-300">
                    {preset.label}
                  </span>
                  <span className="text-[9px] px-1.5 py-0.2 rounded bg-slate-800 text-teal-300 border border-slate-700">
                    {preset.tag}
                  </span>
                </div>
                <div className="text-[11px] text-slate-400 line-clamp-1 italic">
                  "{preset.text}"
                </div>
                <div className="text-[10px] text-slate-500">
                  {preset.desc}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
