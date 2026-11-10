import React, { useState, useRef, useEffect } from "react";
import { Mic, MicOff, Volume2, Sparkles, AlertCircle, RefreshCw } from "lucide-react";

interface VoiceRecorderProps {
  onAudioRecorded: (blob: Blob, sampleText?: string) => void;
  onPresetSelected: (text: string) => void;
  isLoading: boolean;
  keytermsEnabled: boolean;
  onToggleKeyterms: () => void;
}

const PRESET_UTTERANCES = [
  {
    label: "3-Item Typical Order",
    text: "Bhaiya do packet Maggi, ek kilo sugar aur aadha litre milk bhej dena.",
    desc: "2 pkt Maggi + 1 kg Sugar + 0.5 L Milk"
  },
  {
    label: "Ambiguous Order (Chawal)",
    text: "Gupta ji do kilo chawal aur ek packet Tata Salt pack kar do.",
    desc: "Triggers Basmati vs Sona Masoori clarification"
  },
  {
    label: "Colloquial Fractions (Dhai & Dedh)",
    text: "Bhaiya dhai kilo Aashirvaad chakki atta aur dedh kilo toor dal chahiye, ho gaya.",
    desc: "2.5 kg Atta + 1.5 kg Toor Dal + Order completion"
  },
  {
    label: "Snacks & Tea Order",
    text: "Teen packet Parle G biscuit aur aadha kilo Red Label tea dena, bas itna hi.",
    desc: "3 pkt Biscuits + 0.5 kg Tea"
  }
];

export const VoiceRecorder: React.FC<VoiceRecorderProps> = ({
  onAudioRecorded,
  onPresetSelected,
  isLoading,
  keytermsEnabled,
  onToggleKeyterms,
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerIntervalRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
    };
  }, []);

  const startRecording = async () => {
    setErrorMessage(null);
    audioChunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        stream.getTracks().forEach((track) => track.stop());
        onAudioRecorded(audioBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingSeconds(0);

      timerIntervalRef.current = window.setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);
    } catch (err: any) {
      console.warn("Microphone access error:", err);
      setErrorMessage("Microphone permission denied or device unavailable. Use a preset order below for instant testing.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
        timerIntervalRef.current = null;
      }
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Volume2 className="w-5 h-5 text-teal-400" />
            Caller Voice Input
          </h2>
          <p className="text-xs text-slate-400">
            Hinglish speech with Auto-LID, fractional quantities & noise tolerance
          </p>
        </div>

        {/* Keyterms toggle */}
        <button
          onClick={onToggleKeyterms}
          className={`text-xs px-2.5 py-1 rounded-full font-medium border transition-colors flex items-center gap-1.5 ${
            keytermsEnabled
              ? "bg-teal-500/10 text-teal-300 border-teal-500/30"
              : "bg-slate-800 text-slate-400 border-slate-700"
          }`}
          title="Toggles 200 Kirana catalog keyterms bias in ASR beam search"
        >
          <Sparkles className="w-3 h-3 text-teal-400" />
          Catalog Keyterms: {keytermsEnabled ? "ON (v3.0)" : "OFF"}
        </button>
      </div>

      {/* Main record button */}
      <div className="flex flex-col items-center justify-center py-6 bg-slate-950/60 rounded-xl border border-slate-800/80 mb-4">
        <button
          onClick={isRecording ? stopRecording : startRecording}
          disabled={isLoading}
          className={`w-20 h-20 rounded-full flex items-center justify-center transition-all transform ${
            isRecording
              ? "bg-red-500 text-white animate-pulse-ring scale-105 shadow-red-500/30"
              : isLoading
              ? "bg-slate-800 text-slate-500 cursor-not-allowed"
              : "bg-gradient-to-tr from-teal-500 to-sky-500 hover:from-teal-400 hover:to-sky-400 text-white shadow-lg shadow-sky-500/20 active:scale-95"
          }`}
        >
          {isRecording ? <MicOff className="w-8 h-8" /> : <Mic className="w-8 h-8" />}
        </button>

        <div className="mt-3 text-center">
          {isRecording ? (
            <div className="flex items-center gap-2 text-red-400 text-sm font-medium animate-pulse">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500"></span>
              Recording... 00:{recordingSeconds < 10 ? `0${recordingSeconds}` : recordingSeconds} (Click to Stop)
            </div>
          ) : isLoading ? (
            <div className="flex items-center gap-2 text-sky-400 text-sm font-medium">
              <RefreshCw className="w-4 h-4 animate-spin" />
              Processing audio via Gnani AI pipeline...
            </div>
          ) : (
            <span className="text-slate-400 text-sm">
              Click microphone to speak order in Hinglish or Hindi
            </span>
          )}
        </div>
      </div>

      {errorMessage && (
        <div className="mb-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg flex items-start gap-2 text-amber-300 text-xs">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Preset orders for fast evaluation */}
      <div>
        <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
          <span className="font-medium text-slate-300">Or test with preset phone order:</span>
          <span>Click to evaluate</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {PRESET_UTTERANCES.map((preset, idx) => (
            <button
              key={idx}
              onClick={() => onPresetSelected(preset.text)}
              disabled={isLoading || isRecording}
              className="text-left p-2.5 bg-slate-800/70 hover:bg-slate-800 border border-slate-700/60 hover:border-sky-500/40 rounded-lg transition-all group"
            >
              <div className="text-xs font-semibold text-slate-200 group-hover:text-sky-300">
                {preset.label}
              </div>
              <div className="text-[11px] text-slate-400 truncate mt-0.5">
                "{preset.text}"
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
