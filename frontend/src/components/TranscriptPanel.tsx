import React from "react";
import { FileText, Cpu, CheckCircle2, ShieldCheck, HelpCircle, RotateCcw, AlertTriangle, Sparkles, Tag } from "lucide-react";

interface ParsedItem {
  product: string;
  quantity: number;
  unit: string;
  raw_clause?: string;
}

export interface RepairEvent {
  original_phrase: string;
  action: string;
  product: string;
  previous_quantity?: number;
  new_quantity?: number;
  explanation: string;
}

interface TranscriptPanelProps {
  transcript: string;
  normalizedTranscript?: string;
  isMock: boolean;
  model: string;
  parsedItems: ParsedItem[];
  isOrderComplete: boolean;
  repairsApplied?: RepairEvent[];
  detectedIntent?: string;
}

export const TranscriptPanel: React.FC<TranscriptPanelProps> = ({
  transcript,
  normalizedTranscript,
  isMock,
  model,
  parsedItems,
  isOrderComplete,
  repairsApplied = [],
  detectedIntent = "ORDER"
}) => {
  if (!transcript) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2 mb-2">
          <FileText className="w-5 h-5 text-sky-400" />
          Transcription & Speech NLP
        </h2>
        <div className="text-center py-8 text-slate-500 text-sm">
          Awaiting spoken order or preset selection above...
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
      {/* Header and badges */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <FileText className="w-5 h-5 text-sky-400" />
          Transcription & Extraction
        </h2>

        <div className="flex items-center gap-2 flex-wrap">
          {detectedIntent === "PRICE_INQUIRY" && (
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/20 flex items-center gap-1 font-semibold">
              <Tag className="w-3 h-3 text-amber-400" />
              Bhav Pucho: Rate Check
            </span>
          )}

          {detectedIntent === "BUDGET_QUERY" && (
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 flex items-center gap-1 font-semibold">
              <Sparkles className="w-3 h-3 text-emerald-400" />
              Budget Cap Optimization
            </span>
          )}

          <span className="text-[11px] px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-300 border border-sky-500/20 flex items-center gap-1">
            <Cpu className="w-3 h-3 text-sky-400" />
            {model} Auto-LID
          </span>

          <span
            className={`text-[11px] px-2 py-0.5 rounded-full border flex items-center gap-1 ${
              isMock
                ? "bg-amber-500/10 text-amber-300 border-amber-500/20"
                : "bg-emerald-500/10 text-emerald-300 border-emerald-500/20"
            }`}
          >
            {isMock ? (
              <>
                <HelpCircle className="w-3 h-3" />
                Demo / Mock Mode
              </>
            ) : (
              <>
                <ShieldCheck className="w-3 h-3" />
                Live Gnani Prisma STT
              </>
            )}
          </span>
        </div>
      </div>

      {/* Raw Transcript */}
      <div>
        <div className="text-xs font-medium text-slate-400 mb-1">Raw Spoken Speech:</div>
        <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-slate-100 text-sm font-medium leading-relaxed font-hindi">
          "{transcript}"
        </div>
      </div>

      {/* Normalized Transcript (with numerals transformed) */}
      {normalizedTranscript && normalizedTranscript !== transcript && (
        <div>
          <div className="text-xs font-medium text-slate-400 mb-1 flex items-center justify-between">
            <span>Normalized Numeral Representation:</span>
            <span className="text-[10px] text-teal-400">Fractions & Units Converted</span>
          </div>
          <div className="p-2.5 bg-slate-950/80 rounded-lg border border-teal-500/20 text-teal-200 text-xs font-mono">
            {normalizedTranscript}
          </div>
        </div>
      )}

      {/* Bhasha-Sudhaar Conversational Repair Alert */}
      {repairsApplied && repairsApplied.length > 0 && (
        <div className="p-3 bg-purple-950/40 border border-purple-500/30 rounded-lg space-y-1.5 animate-fade-in">
          <div className="flex items-center gap-2 text-xs font-bold text-purple-300">
            <RotateCcw className="w-4 h-4 text-purple-400 animate-spin-slow" />
            Bhasha-Sudhaar (भाषा-सुधार) Conversational Repair Applied:
          </div>
          <div className="space-y-1">
            {repairsApplied.map((rep, idx) => (
              <div key={idx} className="text-[11px] text-purple-200 bg-purple-900/30 px-2.5 py-1 rounded border border-purple-500/20 flex items-center justify-between">
                <span>{rep.explanation}</span>
                <span className="text-[9px] px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 font-mono">
                  {rep.action}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Extracted items chips */}
      {parsedItems && parsedItems.length > 0 && (
        <div>
          <div className="text-xs font-medium text-slate-400 mb-2">
            Extracted Entities ({parsedItems.length} items detected):
          </div>
          <div className="flex flex-wrap gap-2">
            {parsedItems.map((item, idx) => (
              <div
                key={idx}
                className="px-3 py-1.5 bg-slate-800/90 border border-slate-700 rounded-lg flex items-center gap-2 text-xs"
              >
                <span className="font-semibold text-slate-100">{item.product}</span>
                <span className="px-1.5 py-0.5 rounded bg-sky-500/20 text-sky-300 font-mono text-[11px]">
                  {item.quantity} {item.unit}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Order completion indicator */}
      {isOrderComplete && (
        <div className="p-2.5 bg-emerald-500/10 border border-emerald-500/30 rounded-lg flex items-center gap-2 text-emerald-300 text-xs">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>Caller signaled order completion ("हो गया" / "बस इतना ही"). Cart ready for billing.</span>
        </div>
      )}
    </div>
  );
};
