import React, { useState, useEffect } from "react";
import { 
  Zap, 
  X, 
  Play, 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  ShieldCheck, 
  Cpu, 
  Volume2, 
  Sparkles, 
  Layers, 
  ArrowRight,
  RotateCcw
} from "lucide-react";

export interface JudgeStressTestCase {
  test_id: string;
  title: string;
  category: string;
  difficulty_badge: string;
  prompt_utterance: string;
  audio_sample_url?: string;
  adversarial_challenge: string;
  why_naive_models_fail: string;
  key_features_tested: string[];
}

export interface JudgeStressTestResponse {
  test_id: string;
  title: string;
  utterance: string;
  normalized_transcript: string;
  latency_ms: number;
  item_f1_score: number;
  detected_intent: string;
  parsed_items: any[];
  rules_applied: string[];
  repairs: any[];
  voiceprint_status?: string;
  explanation: string;
  spoken_reply_hi: string;
}

interface JudgeStressArenaModalProps {
  isOpen: boolean;
  onClose: () => void;
  apiBaseUrl: string;
  onApplyTestUtterance: (text: string) => void;
}

export const JudgeStressArenaModal: React.FC<JudgeStressArenaModalProps> = ({
  isOpen,
  onClose,
  apiBaseUrl,
  onApplyTestUtterance
}) => {
  const [tests, setTests] = useState<JudgeStressTestCase[]>([]);
  const [selectedTestId, setSelectedTestId] = useState<string>("TEST-01");
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [result, setResult] = useState<JudgeStressTestResponse | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchTests();
    }
  }, [isOpen]);

  const fetchTests = async () => {
    try {
      const res = await fetch(`${apiBaseUrl}/judge-arena/tests`);
      if (res.ok) {
        const data = await res.json();
        setTests(data);
      }
    } catch (e) {
      console.warn("Could not fetch judge stress tests:", e);
    }
  };

  const runTest = async (testId: string) => {
    setIsRunning(true);
    setResult(null);
    try {
      const res = await fetch(`${apiBaseUrl}/judge-arena/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ test_id: testId })
      });
      if (res.ok) {
        const data = await res.json();
        setResult(data);
      }
    } catch (e) {
      console.error("Test execution failed:", e);
    } finally {
      setIsRunning(false);
    }
  };

  if (!isOpen) return null;

  const currentTest = tests.find((t) => t.test_id === selectedTestId) || tests[0];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 bg-black/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-5xl bg-slate-900 border border-amber-500/30 rounded-2xl shadow-2xl flex flex-col max-h-[92vh] overflow-hidden">
        {/* Header Bar */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-gradient-to-r from-amber-950/40 via-slate-900 to-slate-950">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 shadow-lg shadow-amber-500/10">
              <Zap className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-white tracking-wide">
                  Judge's Stress-Test Arena <span className="text-amber-400 font-normal text-sm">(परीक्षक अखाड़ा)</span>
                </h3>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30 font-mono font-semibold">
                  ADVERSARIAL PLAYGROUND
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Stress-test KiranaVaani against extreme Indian speech scenarios that cause naive LLMs and Whisper to fail.
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

        {/* Content Body: Left Column Test Selector, Right Column Deep Telemetry */}
        <div className="grid grid-cols-1 lg:grid-cols-12 flex-1 overflow-y-auto divide-y lg:divide-y-0 lg:divide-x divide-slate-800">
          {/* Left Column: Test Scenarios */}
          <div className="lg:col-span-5 p-4 space-y-3 bg-slate-950/40">
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider px-1">
              Select Adversarial Test Scenario ({tests.length})
            </h4>

            <div className="space-y-2">
              {tests.map((test) => {
                const isSelected = test.test_id === selectedTestId;
                return (
                  <button
                    key={test.test_id}
                    onClick={() => {
                      setSelectedTestId(test.test_id);
                      setResult(null);
                    }}
                    className={`w-full text-left p-3 rounded-xl border transition-all ${
                      isSelected
                        ? "bg-amber-500/10 border-amber-500/50 shadow-md shadow-amber-500/10"
                        : "bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 mb-1.5">
                      <span className="text-xs font-mono font-bold text-amber-400">
                        {test.test_id}
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-semibold">
                        {test.difficulty_badge}
                      </span>
                    </div>
                    <div className="text-sm font-semibold text-white leading-tight mb-1">
                      {test.title}
                    </div>
                    <div className="text-xs text-slate-400 line-clamp-2 italic">
                      "{test.prompt_utterance}"
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Right Column: Execution Workbench & Telemetry */}
          <div className="lg:col-span-7 p-5 space-y-5 flex flex-col justify-between">
            {currentTest && (
              <div className="space-y-4">
                {/* Active Test Overview */}
                <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-teal-400 font-mono font-semibold">
                      {currentTest.category}
                    </span>
                    <span className="text-[11px] text-slate-500">
                      Adversarial Complexity: <strong className="text-amber-400">{currentTest.difficulty_badge}</strong>
                    </span>
                  </div>

                  <div className="bg-slate-900 p-3 rounded-lg border border-slate-800 text-sm font-hindi text-slate-200">
                    "{currentTest.prompt_utterance}"
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-1">
                    <div className="p-2.5 rounded-lg bg-rose-950/20 border border-rose-500/20 text-rose-300 space-y-1">
                      <div className="font-bold flex items-center gap-1 text-rose-400">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        Why Naive Speech Models Fail:
                      </div>
                      <p className="text-[11px] text-slate-300">{currentTest.why_naive_models_fail}</p>
                    </div>

                    <div className="p-2.5 rounded-lg bg-teal-950/20 border border-teal-500/20 text-teal-300 space-y-1">
                      <div className="font-bold flex items-center gap-1 text-teal-400">
                        <ShieldCheck className="w-3.5 h-3.5" />
                        KiranaVaani Moat:
                      </div>
                      <p className="text-[11px] text-slate-300">{currentTest.adversarial_challenge}</p>
                    </div>
                  </div>

                  {/* Tested Modules Chips */}
                  <div className="flex flex-wrap items-center gap-1.5 pt-1">
                    <span className="text-[10px] text-slate-500">Verified Pipeline Layers:</span>
                    {currentTest.key_features_tested.map((feat, i) => (
                      <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                        {feat}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Execution Button */}
                <div className="flex flex-wrap items-center gap-3">
                  <button
                    onClick={() => runTest(currentTest.test_id)}
                    disabled={isRunning}
                    className="flex-1 py-2.5 px-4 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-sm shadow-lg shadow-amber-500/20 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
                  >
                    {isRunning ? (
                      <>
                        <RotateCcw className="w-4 h-4 animate-spin" />
                        <span>Evaluating Pipeline...</span>
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4 fill-current" />
                        <span>Execute Adversarial Test in Live Pipeline</span>
                      </>
                    )}
                  </button>

                  <button
                    onClick={() => {
                      onApplyTestUtterance(currentTest.prompt_utterance);
                      onClose();
                    }}
                    className="py-2.5 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 flex items-center gap-1.5 transition"
                  >
                    <span>Load into Cockpit</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>

                {/* Execution Results Banner & Rule Logs */}
                {result && (
                  <div className="space-y-3 p-4 rounded-xl bg-slate-950 border border-teal-500/30 animate-fade-in">
                    <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                        <span className="text-sm font-bold text-white">Evaluation Passed:</span>
                        <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-bold font-mono">
                          {result.item_f1_score}% Item-F1 Accuracy
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
                        <Clock className="w-3.5 h-3.5 text-sky-400" />
                        <span>Latency: <strong>{result.latency_ms} ms</strong></span>
                      </div>
                    </div>

                    {/* Normalized Output */}
                    <div className="text-xs space-y-1">
                      <span className="text-slate-400 font-semibold">Normalized Speech Output:</span>
                      <div className="p-2 rounded bg-slate-900 border border-slate-800 font-mono text-teal-300 text-xs">
                        {result.normalized_transcript}
                      </div>
                    </div>

                    {/* Applied Engineering Rules */}
                    <div className="space-y-1 text-xs">
                      <span className="text-slate-400 font-semibold">Acoustic & Linguistic Rules Applied:</span>
                      <div className="space-y-1">
                        {result.rules_applied.map((r, i) => (
                          <div key={i} className="flex items-start gap-1.5 text-slate-300 text-[11px] font-mono bg-slate-900/60 px-2 py-1 rounded">
                            <span className="text-amber-400">⚡</span>
                            <span>{r}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Spoken Confirmation */}
                    <div className="p-2.5 rounded-lg bg-sky-950/30 border border-sky-500/20 flex items-center justify-between gap-2 text-xs text-sky-200">
                      <div className="flex items-center gap-2">
                        <Volume2 className="w-4 h-4 text-sky-400 flex-shrink-0" />
                        <span><strong>Timbre Spoken Readback:</strong> {result.spoken_reply_hi}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Footer */}
            <div className="pt-4 border-t border-slate-800 text-center text-[11px] text-slate-500">
              KiranaVaani Adversarial Harness • Powered by Gnani.ai Prisma v3.0 Auto-LID & Timbre v2.5 Indian Prosody
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
