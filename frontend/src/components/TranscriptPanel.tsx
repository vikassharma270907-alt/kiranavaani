import React from "react";
import { FileText, Cpu, CheckCircle2, ShieldCheck, HelpCircle } from "lucide-react";

interface ParsedItem {
  product: string;
  quantity: number;
  unit: string;
  raw_clause?: string;
}

interface TranscriptPanelProps {
  transcript: string;
  normalizedTranscript?: string;
  isMock: boolean;
  model: string;
  parsedItems: ParsedItem[];
  isOrderComplete: boolean;
}

export const TranscriptPanel: React.FC<TranscriptPanelProps> = ({
  transcript,
  normalizedTranscript,
  isMock,
  model,
  parsedItems,
  isOrderComplete,
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

        <div className="flex items-center gap-2">
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
        <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-slate-100 text-sm font-medium leading-relaxed">
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
