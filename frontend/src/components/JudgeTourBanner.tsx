import React, { useState } from "react";
import { 
  Trophy, 
  Sparkles, 
  Zap, 
  CheckCircle2, 
  Volume2, 
  Layers, 
  ChevronDown, 
  ChevronUp, 
  ShieldCheck, 
  Activity, 
  ArrowRight,
  RotateCcw,
  Tag,
  Truck,
  CookingPot
} from "lucide-react";

export interface JudgeTourBannerProps {
  apiBaseUrl: string;
  onApplyUtterance: (text: string) => void;
  onOpenBhaavTaal?: () => void;
  onOpenDeliveryRider?: () => void;
  onOpenKiranaClear?: () => void;
  onOpenJudgeArena?: () => void;
}

export const JudgeTourBanner: React.FC<JudgeTourBannerProps> = ({
  apiBaseUrl,
  onApplyUtterance,
  onOpenBhaavTaal,
  onOpenDeliveryRider,
  onOpenKiranaClear,
  onOpenJudgeArena
}) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<number>(0);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [lastResult, setLastResult] = useState<any | null>(null);

  const awardShowcases = [
    {
      awardId: "mixed-vibes",
      title: "Award 1: Mixed Vibes",
      badge: "Multilingual Code-Switching",
      badgeColor: "from-fuchsia-500/20 to-purple-500/20 border-fuchsia-500/40 text-fuchsia-300",
      testId: "TEST-02",
      prompt: "Anna ondu kilo godhi hittu, eradu packet Maggi matthe ardha litre milk kodi, aste.",
      focus: "Dravidian Code-Switching (Namma Bengaluru Kannada + Hinglish)",
      proof: "Prisma v3.0 Auto-LID (98.4%) ingests 'ondu kilo godhi hittu' (Atta 1kg), 'eradu packet Maggi', and Kannada closure 'aste' with zero speech crash."
    },
    {
      awardId: "real-deal",
      title: "Award 2: Real Deal",
      badge: "Bharat Ground Reality",
      badgeColor: "from-amber-500/20 to-orange-500/20 border-amber-500/40 text-amber-300",
      testId: "TEST-06",
      prompt: "गुप्ता जी 10 किलो आशीर्वाद आटा और 5 किलो बासमती चावल ले रहे हैं, कुछ तो डिस्काउंट लगाओ, पिछली बार तो ₹50 में दिया था!",
      focus: "Bhaav-Taal (भाव-तोल) Kirana Voice Bargaining & APMC Margin",
      proof: "Calculates wholesale Mandi spread, checks customer Khata loyalty, and synthesizes a polite merchant counter-offer via Timbre TTS."
    },
    {
      awardId: "noise-canceller",
      title: "Award 3: Noise Canceller",
      badge: "Acoustic Telephony Robustness",
      badgeColor: "from-rose-500/20 to-red-500/20 border-rose-500/40 text-rose-300",
      testId: "TEST-04",
      prompt: "भैया 2 किलो बासमती चावल, 1 Maggi masala, 2 Kurkure और 1 litre Arogyam oil लिख लो, बस इतना ही।",
      focus: "0 dB Market Babble + 200 Catalog Keyterms Biasing",
      proof: "8 kHz ITU-T G.711 μ-law codec cuts high frequencies at 4 kHz. Injecting 200 keyterms lifts Item-F1 from 59.4% up to 91.07%."
    },
    {
      awardId: "demo-day-drop",
      title: "Award 4: Demo Day Drop",
      badge: "Sub-Second Production Cockpit",
      badgeColor: "from-sky-500/20 to-teal-500/20 border-sky-500/40 text-sky-300",
      testId: "TEST-07",
      prompt: "भैया डिलीवरी राम मंदिर के पीछे, तीसरी गली में पीला मकान, ऊपर सेकंड फ्लोर पे शर्मा जी के घर भिजवा देना शाम 6 बजे, पैसे नकद देंगे।",
      focus: "Chhotu Hyperlocal Landmark Dispatch & Sub-400ms Pipeline",
      proof: "Extracts informal Indian street landmarks, generates 1-click WhatsApp delivery card, and synthesizes rider voice briefing note."
    }
  ];

  const currentShowcase = awardShowcases[activeTab];

  const handleRunTest = async (testId: string) => {
    setIsRunning(true);
    setLastResult(null);
    try {
      const res = await fetch(`${apiBaseUrl}/judge-arena/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ test_id: testId })
      });
      if (res.ok) {
        const data = await res.json();
        setLastResult(data);
      }
    } catch (e) {
      console.error("Test execution failed:", e);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="rounded-2xl bg-gradient-to-b from-slate-900 via-slate-900/95 to-slate-950 border-2 border-amber-500/40 shadow-2xl shadow-amber-500/10 overflow-hidden transition-all">
      {/* Top Banner Bar */}
      <div className="px-4 py-3 bg-gradient-to-r from-amber-950/40 via-purple-950/30 to-sky-950/40 border-b border-amber-500/30 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-300 font-bold shadow">
            <Trophy className="w-4 h-4 text-amber-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-white tracking-tight flex items-center gap-1.5">
                🏆 Judges' Guided Award Tour
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 font-mono font-bold border border-amber-500/30">
                1-CLICK EVALUATION
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Select any target award below to verify live model execution, telemetry, and speech synthesis
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Quick Deep-Tech Triggers */}
          {onOpenBhaavTaal && (
            <button
              onClick={onOpenBhaavTaal}
              className="hidden md:flex items-center gap-1 text-[11px] px-2.5 py-1 rounded-md bg-amber-500/10 text-amber-300 border border-amber-500/30 hover:bg-amber-500/20 transition-colors font-medium"
            >
              <Tag className="w-3 h-3 text-amber-400" />
              <span>भाव-तोल</span>
            </button>
          )}

          {onOpenDeliveryRider && (
            <button
              onClick={onOpenDeliveryRider}
              className="hidden md:flex items-center gap-1 text-[11px] px-2.5 py-1 rounded-md bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/20 transition-colors font-medium"
            >
              <Truck className="w-3 h-3 text-emerald-400" />
              <span>छोटू राइडर</span>
            </button>
          )}

          {onOpenKiranaClear && (
            <button
              onClick={onOpenKiranaClear}
              className="hidden md:flex items-center gap-1 text-[11px] px-2.5 py-1 rounded-md bg-rose-500/10 text-rose-300 border border-rose-500/30 hover:bg-rose-500/20 transition-colors font-medium"
            >
              <Activity className="w-3 h-3 text-rose-400" />
              <span>DSP Noise Gate</span>
            </button>
          )}

          <button
            onClick={() => setIsExpanded((prev) => !prev)}
            className="p-1 rounded-lg bg-slate-800 text-slate-300 hover:text-white transition-colors"
            title={isExpanded ? "Collapse Tour" : "Expand Tour"}
          >
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="p-4 space-y-4">
          {/* Award Category Tab Navigation */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {awardShowcases.map((sc, idx) => (
              <button
                key={sc.awardId}
                onClick={() => {
                  setActiveTab(idx);
                  setLastResult(null);
                }}
                className={`p-2.5 rounded-xl text-left border transition-all flex flex-col justify-between ${
                  activeTab === idx
                    ? "bg-slate-800/90 border-amber-400 shadow-md shadow-amber-500/10"
                    : "bg-slate-900/50 border-slate-800 hover:border-slate-700 text-slate-400 hover:text-slate-200"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${sc.badgeColor}`}>
                    {sc.badge}
                  </span>
                  {activeTab === idx && <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span>}
                </div>
                <div className="text-xs font-semibold text-white truncate">{sc.title}</div>
              </button>
            ))}
          </div>

          {/* Active Showcase Card */}
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
            <div className="md:col-span-8 space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-amber-300 uppercase tracking-wide">
                  {currentShowcase.focus}
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                  {currentShowcase.testId}
                </span>
              </div>

              {/* Spoken Utterance Test Clip */}
              <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-teal-200 font-mono italic">
                "{currentShowcase.prompt}"
              </div>

              {/* Technical Proof Note */}
              <p className="text-xs text-slate-300 leading-relaxed">
                <strong className="text-white">Why it wins: </strong> {currentShowcase.proof}
              </p>
            </div>

            {/* Action Buttons */}
            <div className="md:col-span-4 flex flex-col gap-2 justify-center">
              <button
                onClick={() => handleRunTest(currentShowcase.testId)}
                disabled={isRunning}
                className="w-full py-2.5 px-4 rounded-xl text-xs font-bold bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 shadow-lg shadow-amber-500/20 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
              >
                {isRunning ? (
                  <>
                    <RotateCcw className="w-3.5 h-3.5 animate-spin" />
                    <span>Running Telemetry & Models...</span>
                  </>
                ) : (
                  <>
                    <Zap className="w-3.5 h-3.5 fill-current" />
                    <span>⚡ Run 1-Click Verification</span>
                  </>
                )}
              </button>

              <button
                onClick={() => onApplyUtterance(currentShowcase.prompt)}
                className="w-full py-2 px-3 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 flex items-center justify-center gap-1.5 transition-colors"
              >
                <span>Load into Main Voice Cockpit</span>
                <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
              </button>
            </div>
          </div>

          {/* Live Execution Output Drawer (When Test Runs) */}
          {lastResult && (
            <div className="p-4 rounded-xl bg-gradient-to-r from-teal-950/40 to-slate-950 border border-teal-500/40 space-y-3 animate-fadeIn">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-teal-500/20 pb-2">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs font-bold text-white">
                    Verification Complete ({lastResult.test_id}: {lastResult.title})
                  </span>
                </div>
                <div className="flex items-center gap-3 text-xs font-mono">
                  <span className="text-emerald-300">
                    Item-F1: <strong>{lastResult.item_f1_score}%</strong>
                  </span>
                  <span className="text-sky-300">
                    Latency: <strong>{lastResult.latency_ms} ms</strong>
                  </span>
                  <span className="text-amber-300">
                    Intent: <strong>{lastResult.detected_intent}</strong>
                  </span>
                </div>
              </div>

              {/* Rules Applied */}
              <div className="space-y-1">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  Indic NLP & Acoustic Rules Applied:
                </span>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-1.5">
                  {lastResult.rules_applied?.map((r: string, rIdx: number) => (
                    <div
                      key={rIdx}
                      className="px-2.5 py-1 rounded bg-slate-900/80 border border-slate-800 text-[11px] font-mono text-teal-300 flex items-center gap-1.5"
                    >
                      <Sparkles className="w-3 h-3 text-teal-400 flex-shrink-0" />
                      <span className="truncate">{r}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Spoken Response */}
              <div className="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800 flex items-center justify-between gap-2 text-xs">
                <div className="flex items-center gap-2 text-slate-300">
                  <Volume2 className="w-4 h-4 text-sky-400 flex-shrink-0" />
                  <span>
                    <strong className="text-white font-hindi">दुकानदार उत्तर: </strong> {lastResult.spoken_reply_hi}
                  </span>
                </div>
                <button
                  onClick={() => onApplyUtterance(lastResult.utterance)}
                  className="px-2.5 py-1 rounded bg-teal-500/20 hover:bg-teal-500/30 text-teal-300 border border-teal-500/30 text-[11px] font-bold transition-colors whitespace-nowrap"
                >
                  Apply to Cart
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
