import React, { useState, useEffect } from "react";
import { BookOpen, X, Phone, DollarSign, CheckCircle2, MessageSquare, Play, Pause, Volume2, ShieldAlert, Sparkles, Send } from "lucide-react";

export interface KhataCustomer {
  customer_id: string;
  name: string;
  phone: string;
  current_balance_inr: number;
  last_order_date: string;
  orders_count: number;
  trust_tier: string;
  recent_items: string[];
}

interface KhataLedgerDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  apiBaseUrl: string;
}

export const KhataLedgerDrawer: React.FC<KhataLedgerDrawerProps> = ({
  isOpen,
  onClose,
  apiBaseUrl
}) => {
  const [customers, setCustomers] = useState<KhataCustomer[]>([]);
  const [totalOutstanding, setTotalOutstanding] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [selectedCustomer, setSelectedCustomer] = useState<KhataCustomer | null>(null);
  const [settleAmount, setSettleAmount] = useState<string>("");
  const [settleMessage, setSettleMessage] = useState<string | null>(null);
  const [reminderAudioB64, setReminderAudioB64] = useState<string | null>(null);
  const [reminderText, setReminderText] = useState<string | null>(null);
  const [isPlayingAudio, setIsPlayingAudio] = useState<boolean>(false);
  const audioRef = React.useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchKhataCustomers();
    }
  }, [isOpen]);

  const fetchKhataCustomers = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${apiBaseUrl}/khata/customers`);
      if (res.ok) {
        const data = await res.json();
        setCustomers(data.customers || []);
        setTotalOutstanding(data.total_outstanding_inr || 0);
      }
    } catch (e) {
      console.warn("Failed to fetch khata customers, using fallback data:", e);
      setCustomers([
        {
          customer_id: "CUST-001",
          name: "Sharma Ji (शर्मा जी)",
          phone: "+91 98111-23456",
          current_balance_inr: 420.0,
          last_order_date: "10-Nov-2026",
          orders_count: 14,
          trust_tier: "A (अति-विश्वसनीय)",
          recent_items: ["Aashirvaad Atta (5kg)", "Tata Salt (1kg)", "Fortune Oil (1L)"]
        },
        {
          customer_id: "CUST-002",
          name: "Verma Ji (वर्मा जी)",
          phone: "+91 98222-34567",
          current_balance_inr: 1150.0,
          last_order_date: "06-Nov-2026",
          orders_count: 8,
          trust_tier: "B (साप्ताहिक हिसाब)",
          recent_items: ["India Gate Basmati (5kg)", "Amul Pure Cow Ghee (500ml)"]
        },
        {
          customer_id: "CUST-003",
          name: "Patel Sahab (पटेल साहब)",
          phone: "+91 98333-45678",
          current_balance_inr: 280.0,
          last_order_date: "09-Nov-2026",
          orders_count: 22,
          trust_tier: "A (अति-विश्वसनीय)",
          recent_items: ["Tata Tea Gold (250g)", "Madhur Sugar (1kg)"]
        },
        {
          customer_id: "CUST-004",
          name: "Sunita Devi (सुनीता देवी)",
          phone: "+91 98444-56789",
          current_balance_inr: 540.0,
          last_order_date: "08-Nov-2026",
          orders_count: 11,
          trust_tier: "A (समय पर भुगतान)",
          recent_items: ["Toor Dal (1kg)", "Parle-G (2 pkt)", "Amul Milk (1L)"]
        }
      ]);
      setTotalOutstanding(2390.0);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSettle = async (custId: string) => {
    const amt = parseFloat(settleAmount);
    if (isNaN(amt) || amt <= 0) return;

    try {
      const res = await fetch(`${apiBaseUrl}/khata/settle`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer_id: custId,
          amount_paid_inr: amt,
          payment_mode: "upi"
        })
      });

      if (res.ok) {
        const data = await res.json();
        setSettleMessage(data.message_hi);
        setSettleAmount("");
        fetchKhataCustomers();
      }
    } catch (e) {
      console.warn("Settlement error:", e);
    }
  };

  const handleGenerateVoiceReminder = async (custId: string) => {
    setIsLoading(true);
    setReminderText(null);
    setReminderAudioB64(null);

    try {
      const res = await fetch(`${apiBaseUrl}/khata/voice-reminder`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ customer_id: custId })
      });

      if (res.ok) {
        const data = await res.json();
        setReminderText(data.whatsapp_text);
        if (data.audio_base64) {
          setReminderAudioB64(data.audio_base64);
          const audio = new Audio(`data:audio/wav;base64,${data.audio_base64}`);
          audioRef.current = audio;
          audio.onended = () => setIsPlayingAudio(false);
          audio.play().then(() => setIsPlayingAudio(true)).catch(e => console.warn(e));
        }
      }
    } catch (e) {
      console.warn("Reminder error:", e);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex justify-end transition-opacity">
      <div className="w-full max-w-xl bg-slate-900 border-l border-slate-800 h-full flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                Kirana Khata 2.0 <span className="text-amber-400 font-hindi font-normal">(उधार बहीखाता)</span>
              </h2>
              <p className="text-xs text-slate-400">
                Gupta Kirana Store • Customer Credit Ledger & Voice Reminders
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Total Outstanding Metric Card */}
        <div className="p-4 bg-slate-950/40 border-b border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-[11px] text-slate-400 uppercase font-semibold">Total Store Outstanding (कुल उधारी)</div>
            <div className="text-2xl font-bold text-amber-300 font-mono">₹{totalOutstanding.toFixed(2)}</div>
          </div>
          <div className="text-right">
            <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 font-medium">
              4 Active Customer Accounts
            </span>
          </div>
        </div>

        {/* Customer Accounts List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {settleMessage && (
            <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-500/40 text-emerald-200 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span>{settleMessage}</span>
            </div>
          )}

          {customers.map((c) => (
            <div
              key={c.customer_id}
              className={`p-4 rounded-xl border transition-all ${
                selectedCustomer?.customer_id === c.customer_id
                  ? "bg-slate-800/90 border-amber-500/60 shadow-lg"
                  : "bg-slate-950/80 border-slate-800 hover:border-slate-700"
              }`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-sm font-bold text-white flex items-center gap-2">
                    {c.name}
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 font-mono">
                      {c.customer_id}
                    </span>
                  </div>
                  <div className="text-xs text-slate-400 font-mono mt-0.5">{c.phone}</div>
                </div>

                <div className="text-right">
                  <div className="text-base font-bold text-amber-300 font-mono">
                    ₹{c.current_balance_inr.toFixed(2)}
                  </div>
                  <span className="text-[10px] text-slate-400">{c.trust_tier}</span>
                </div>
              </div>

              {/* Recent Orders info */}
              <div className="mt-2.5 pt-2 border-t border-slate-800/80 text-[11px] text-slate-400 flex flex-wrap gap-1">
                <span>Recent items:</span>
                {c.recent_items.map((it, idx) => (
                  <span key={idx} className="px-1.5 py-0.2 rounded bg-slate-900 border border-slate-800 text-slate-300">
                    {it}
                  </span>
                ))}
              </div>

              {/* Action Buttons: Settle & Voice Reminder */}
              <div className="mt-3 flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-800/60">
                <div className="flex items-center gap-1.5">
                  <input
                    type="number"
                    placeholder="₹ Amount"
                    value={selectedCustomer?.customer_id === c.customer_id ? settleAmount : ""}
                    onChange={(e) => {
                      setSelectedCustomer(c);
                      setSettleAmount(e.target.value);
                    }}
                    className="w-24 px-2 py-1 text-xs rounded bg-slate-900 border border-slate-700 text-white font-mono"
                  />
                  <button
                    onClick={() => handleSettle(c.customer_id)}
                    className="px-2.5 py-1 text-xs font-semibold rounded bg-emerald-600 hover:bg-emerald-500 text-white"
                  >
                    जमा करें (Settle)
                  </button>
                </div>

                <button
                  onClick={() => handleGenerateVoiceReminder(c.customer_id)}
                  className="px-2.5 py-1 text-xs font-semibold rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 flex items-center gap-1.5 transition-colors"
                >
                  <Volume2 className="w-3.5 h-3.5 text-amber-400" />
                  WhatsApp Voice Reminder
                </button>
              </div>
            </div>
          ))}

          {/* Spoken Reminder Preview Card */}
          {reminderText && (
            <div className="mt-4 p-4 rounded-xl bg-slate-950 border border-amber-500/40 space-y-2.5">
              <div className="flex items-center justify-between text-xs font-bold text-amber-200">
                <span className="flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                  Synthesized Timbre Voice Note & WhatsApp Slip
                </span>
                {reminderAudioB64 && (
                  <button
                    onClick={() => {
                      if (audioRef.current) {
                        if (isPlayingAudio) {
                          audioRef.current.pause();
                          setIsPlayingAudio(false);
                        } else {
                          audioRef.current.play();
                          setIsPlayingAudio(true);
                        }
                      }
                    }}
                    className="text-xs px-2 py-0.5 rounded bg-amber-500 text-slate-950 font-bold flex items-center gap-1"
                  >
                    {isPlayingAudio ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3" />}
                    {isPlayingAudio ? "Pause" : "Play Audio"}
                  </button>
                )}
              </div>

              <pre className="text-[11px] text-slate-300 bg-slate-900/90 p-2.5 rounded font-sans whitespace-pre-wrap border border-slate-800 leading-relaxed">
                {reminderText}
              </pre>

              <button
                onClick={() => {
                  navigator.clipboard.writeText(reminderText);
                  alert("WhatsApp Payment Reminder copied to clipboard!");
                }}
                className="w-full py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold flex items-center justify-center gap-2"
              >
                <Send className="w-3.5 h-3.5" />
                Copy & Send to Customer on WhatsApp
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
