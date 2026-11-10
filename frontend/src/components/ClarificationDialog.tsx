import React from "react";
import { AlertTriangle, Check, HelpCircle } from "lucide-react";

export interface ClarificationOption {
  sku_id: string;
  name_en: string;
  name_hi: string;
  category?: string;
  quantity: number;
  unit: string;
  price_inr: number;
}

export interface ClarificationQuestion {
  family: string;
  spoken_phrase: string;
  question_hi: string;
  question_en: string;
  options: ClarificationOption[];
  confidence: number;
}

export interface SubstitutionSuggestion {
  original_item_name: string;
  out_of_stock_sku: {
    sku_id: string;
    name_en: string;
    name_hi: string;
    price_inr: number;
    unit: string;
  };
  substitute_sku: {
    sku_id: string;
    name_en: string;
    name_hi: string;
    category?: string;
    price_inr: number;
    unit: string;
  };
  reason_hi: string;
  reason_en: string;
  spoken_prompt_hi: string;
  spoken_prompt_en: string;
}

interface ClarificationDialogProps {
  clarifications: ClarificationQuestion[];
  onResolveOption: (chosenOption: ClarificationOption) => void;
  substitutions?: SubstitutionSuggestion[];
  onAcceptSubstitution?: (sub: SubstitutionSuggestion) => void;
}

export const ClarificationDialog: React.FC<ClarificationDialogProps> = ({
  clarifications,
  onResolveOption,
  substitutions = [],
  onAcceptSubstitution,
}) => {
  const hasContent = (clarifications && clarifications.length > 0) || (substitutions && substitutions.length > 0);
  if (!hasContent) return null;

  return (
    <div className="bg-amber-950/40 border-2 border-amber-500/50 rounded-xl p-5 shadow-xl space-y-4">
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-lg bg-amber-500/20 text-amber-400">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <div>
          <h3 className="text-base font-bold text-amber-200 flex items-center gap-2">
            Clarification Required (अस्पष्ट ऑर्डर)
          </h3>
          <p className="text-xs text-amber-300/80 mt-0.5">
            Ambiguous product match detected. System paused cart addition to prevent order error.
          </p>
        </div>
      </div>

      {clarifications.map((q, idx) => (
        <div key={idx} className="bg-slate-900/90 rounded-lg p-4 border border-amber-500/30 space-y-3">
          <div>
            <div className="text-xs font-semibold text-slate-300">
              Spoken Clause: <span className="text-amber-300 italic">"{q.spoken_phrase}"</span>
            </div>
            <div className="text-sm font-medium text-amber-100 mt-1">
              {q.question_hi}
            </div>
            <div className="text-xs text-slate-400 mt-0.5">
              {q.question_en}
            </div>
          </div>

          <div className="pt-2">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-300 mb-2">
              <span>Select or speak intended grocery item:</span>
              <span className="text-[10px] text-teal-400 font-mono">🎙️ Hands-free Voice Answer supported</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {q.options.map((opt) => (
                <button
                  key={opt.sku_id}
                  onClick={() => onResolveOption(opt)}
                  className="text-left p-3 rounded-lg bg-slate-800 hover:bg-teal-900/40 border border-slate-700 hover:border-teal-400/50 transition-all flex items-center justify-between group"
                >
                  <div>
                    <div className="text-xs font-semibold text-white group-hover:text-teal-300">
                      {opt.name_hi}
                    </div>
                    <div className="text-[11px] text-slate-400">
                      {opt.name_en} ({opt.quantity} {opt.unit})
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-bold text-teal-400">
                      ₹{opt.price_inr}
                    </span>
                    <div className="text-[10px] text-slate-500">per {opt.unit}</div>
                  </div>
                </button>
              ))}
            </div>
            <div className="mt-2 text-[11px] text-slate-400 italic bg-slate-950/60 p-2 rounded border border-slate-800 flex items-center gap-1.5">
              <span>💡</span>
              <span><strong>Spoken Clarification:</strong> Simply click the microphone above and speak <em>"बासमती वाला"</em> or <em>"सोना मसूरी"</em> to resolve without clicking!</span>
            </div>
          </div>
        </div>
      ))}

      {/* Out-of-Stock Intelligent Substitutions */}
      {substitutions.map((sub, idx) => (
        <div key={`sub-${idx}`} className="bg-slate-900/90 rounded-lg p-4 border border-rose-500/40 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-rose-300 flex items-center gap-1">
              ⚠️ अनुपलब्ध सामान का विकल्प (Out-of-Stock Substitution)
            </span>
            <span className="text-[10px] px-1.5 py-0.2 rounded bg-rose-500/10 text-rose-300 border border-rose-500/20 font-mono">
              Stockout Detected
            </span>
          </div>

          <div>
            <div className="text-sm font-semibold text-white">
              "{sub.spoken_prompt_hi}"
            </div>
            <div className="text-xs text-slate-400 mt-0.5">
              {sub.spoken_prompt_en}
            </div>
          </div>

          <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-between">
            <div>
              <div className="text-xs line-through text-slate-500">
                {sub.out_of_stock_sku.name_en} ({sub.out_of_stock_sku.name_hi})
              </div>
              <div className="text-xs font-bold text-teal-300 mt-0.5">
                ➡️ Recommended: {sub.substitute_sku.name_en} ({sub.substitute_sku.name_hi})
              </div>
            </div>

            {onAcceptSubstitution && (
              <button
                onClick={() => onAcceptSubstitution(sub)}
                className="px-3 py-1.5 rounded-lg bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold text-xs shadow-lg shadow-teal-500/20 transition-all flex items-center gap-1"
              >
                <Check className="w-3.5 h-3.5" />
                स्वीकार करें (Add Substitute ₹{sub.substitute_sku.price_inr})
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};
