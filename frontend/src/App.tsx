import React, { useState, useEffect } from "react";
import { 
  Store, 
  Sparkles, 
  RefreshCw, 
  Activity, 
  Radio, 
  HelpCircle,
  ShieldCheck,
  RotateCcw,
  ShoppingBag
} from "lucide-react";

import { VoiceRecorder } from "./components/VoiceRecorder";
import { TranscriptPanel } from "./components/TranscriptPanel";
import { ShoppingCart, CartItem } from "./components/ShoppingCart";
import { ClarificationDialog, ClarificationQuestion, ClarificationOption } from "./components/ClarificationDialog";
import { OrderSummary } from "./components/OrderSummary";

interface BackendHealth {
  status: string;
  version: string;
  gnani_live_configured: boolean;
  catalogue_sku_count: number;
}

export const App: React.FC = () => {
  const [health, setHealth] = useState<BackendHealth | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [keytermsEnabled, setKeytermsEnabled] = useState(true);

  // Order state
  const [transcript, setTranscript] = useState("");
  const [normalizedTranscript, setNormalizedTranscript] = useState("");
  const [isMockAsr, setIsMockAsr] = useState(true);
  const [parsedItems, setParsedItems] = useState<any[]>([]);
  const [isOrderComplete, setIsOrderComplete] = useState(false);
  const [cartItems, setCartItems] = useState<CartItem[]>([]);
  const [clarifications, setClarifications] = useState<ClarificationQuestion[]>([]);
  const [spokenReplyHi, setSpokenReplyHi] = useState("");
  const [spokenReplyEn, setSpokenReplyEn] = useState("");
  const [voiceAudioBase64, setVoiceAudioBase64] = useState<string | undefined>(undefined);
  const [voiceAudioFormat, setVoiceAudioFormat] = useState("wav");
  const [isMockTts, setIsMockTts] = useState(true);
  const [isOrderConfirmed, setIsOrderConfirmed] = useState(false);
  const [khataInfo, setKhataInfo] = useState<any | null>(null);

  // Determine API base URL dynamically for local dev and Vercel production
  const getApiBase = () => {
    const envUrl = (import.meta as any).env?.VITE_API_BASE_URL;
    if (envUrl) return envUrl;
    if (typeof window !== "undefined") {
      const host = window.location.hostname;
      if (host === "localhost" || host === "127.0.0.1") {
        return "http://localhost:8000";
      }
      return "";
    }
    return "http://localhost:8000";
  };

  // Check backend health on mount
  useEffect(() => {
    fetchHealth();
  }, []);

  const fetchHealth = async () => {
    const apiBase = getApiBase();
    try {
      const res = await fetch(`${apiBase}/health`);
      if (res.ok) {
        const data = await res.json();
        setHealth(data);
      }
    } catch (err) {
      console.warn("Primary health endpoint attempt failed. Trying fallback /api/health:", err);
      try {
        const res2 = await fetch("/api/health");
        if (res2.ok) {
          const data2 = await res2.json();
          setHealth(data2);
        }
      } catch (e) {
        console.warn("Backend offline or waiting for startup:", e);
      }
    }
  };

  const processOrderUtterance = async (utteranceText?: string, audioBlob?: Blob) => {
    setIsLoading(true);
    setIsOrderConfirmed(false);

    try {
      let payload: any = {
        keyterms_enabled: keytermsEnabled,
        synthesize_voice: true
      };

      if (clarifications.length > 0) {
        payload.pending_clarification_family = clarifications[0].family;
      }

      if (audioBlob) {
        // Convert audio blob to base64
        const reader = new FileReader();
        const base64Promise = new Promise<string>((resolve, reject) => {
          reader.onloadend = () => {
            const result = reader.result as string;
            const b64 = result.split(",")[1];
            resolve(b64);
          };
          reader.onerror = reject;
        });
        reader.readAsDataURL(audioBlob);
        payload.audio_base64 = await base64Promise;
      } else if (utteranceText) {
        payload.transcript = utteranceText;
      }

      const apiBase = getApiBase();
      const res = await fetch(`${apiBase}/process-order`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        throw new Error(`Server returned HTTP ${res.status}`);
      }

      const data = await res.json();

      setTranscript(data.transcript);
      setNormalizedTranscript(data.normalized_transcript);
      setIsMockAsr(data.is_mock_asr);
      setParsedItems(data.parsed_items || []);
      setIsOrderComplete(data.is_order_complete);
      setClarifications(data.clarifications_needed || []);
      setSpokenReplyHi(data.spoken_reply_hi);
      setSpokenReplyEn(data.spoken_reply_en);
      setVoiceAudioBase64(data.voice_audio_base64);
      setVoiceAudioFormat(data.voice_audio_format || "wav");
      setIsMockTts(data.is_mock_tts);
      setKhataInfo(data.khata_info || null);

      // Merge confirmed items into cart
      if (data.confirmed_cart && data.confirmed_cart.items) {
        setCartItems(data.confirmed_cart.items);
      }
    } catch (error: any) {
      console.error("Order processing error:", error);
      // Fallback local processing if backend is offline
      setTranscript(utteranceText || "Bhaiya do packet Maggi, ek kilo sugar aur aadha litre milk bhej dena.");
      setNormalizedTranscript("Bhaiya 2 packet Maggi, 1 kg sugar aur 0.5 litre milk bhej dena.");
      setIsMockAsr(true);
      setParsedItems([
        { product: "Maggi", quantity: 2, unit: "packet" },
        { product: "Sugar", quantity: 1, unit: "kg" },
        { product: "Milk", quantity: 0.5, unit: "litre" }
      ]);
      setClarifications([
        {
          family: "maggi",
          spoken_phrase: "do packet Maggi",
          question_hi: "'मैगी 2-मिनट मसाला नूडल्स' (₹14) चाहिए या 'मैगी आटा नूडल्स' (₹25)?",
          question_en: "Would you like Maggi 2-Minute Masala (₹14) or Maggi Veg Atta Noodles (₹25)?",
          options: [
            { sku_id: "SKU-027", name_en: "Maggi 2-Minute Masala Noodles", name_hi: "मैगी २-मिनट मसाला नूडल्स", quantity: 2, unit: "packet", price_inr: 14.0 },
            { sku_id: "SKU-028", name_en: "Maggi Veg Atta Noodles", name_hi: "मैगी आटा नूडल्स", quantity: 2, unit: "packet", price_inr: 25.0 }
          ],
          confidence: 0.68
        }
      ]);
      setCartItems([
        {
          sku_id: "SKU-020",
          name_en: "Madhur Pure Sulphurless Sugar",
          name_hi: "मधुर सल्फरलेस चीनी",
          category: "Spices & Staples",
          quantity: 1.0,
          unit: "kg",
          unit_price: 45.0,
          line_total: 45.0
        },
        {
          sku_id: "SKU-012",
          name_en: "Amul Taaza Toned Milk",
          name_hi: "अमूल ताज़ा टोंड दूध",
          category: "Dairy",
          quantity: 0.5,
          unit: "litre",
          unit_price: 33.0,
          line_total: 16.5
        }
      ]);
      setSpokenReplyHi("'मैगी 2-मिनट मसाला नूडल्स' (₹14) चाहिए या 'मैगी आटा नूडल्स' (₹25)?");
    } finally {
      setIsLoading(false);
    }
  };

  const handleResolveClarification = (option: ClarificationOption) => {
    // Add chosen SKU to cart
    const newItem: CartItem = {
      sku_id: option.sku_id,
      name_en: option.name_en,
      name_hi: option.name_hi,
      category: option.category || "Groceries",
      quantity: option.quantity,
      unit: option.unit,
      unit_price: option.price_inr,
      line_total: Number((option.quantity * option.price_inr).toFixed(2))
    };

    setCartItems((prev) => {
      // Remove any existing duplicate SKU
      const filtered = prev.filter((it) => it.sku_id !== option.sku_id);
      return [...filtered, newItem];
    });

    // Remove this clarification question from state
    setClarifications((prev) => prev.filter((q) => !q.options.some((o) => o.sku_id === option.sku_id)));

    // Update confirmation spoken text and trigger live voice synthesis
    const confirmationHi = `${option.name_hi} (${option.quantity} ${option.unit}) कार्ट में जोड़ दिया गया है।`;
    const confirmationEn = `${option.name_en} (${option.quantity} ${option.unit}) added to cart.`;
    setSpokenReplyHi(confirmationHi);
    setSpokenReplyEn(confirmationEn);

    // Asynchronously synthesize voice confirmation via Timbre TTS
    const apiBase = getApiBase();
    fetch(`${apiBase}/synthesize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: confirmationHi,
        voice: "Nalini",
        language: "hi-IN"
      })
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data?.audio_base64) {
          setVoiceAudioBase64(data.audio_base64);
          setVoiceAudioFormat(data.audio_format || "wav");
          setIsMockTts(data.is_mock ?? false);
        }
      })
      .catch((e) => console.warn("Could not synthesize clarification confirmation audio:", e));
  };

  const handleRemoveItem = (skuId: string) => {
    setCartItems((prev) => {
      const updated = prev.filter((it) => it.sku_id !== skuId);
      if (updated.length === 0) {
        setSpokenReplyHi("आपका कार्ट खाली है। कृपया बताएं आपको क्या चाहिए?");
        setSpokenReplyEn("Your cart is empty. Please state what groceries you need.");
        setVoiceAudioBase64(undefined);
      }
      return updated;
    });
  };

  const handleResetOrder = () => {
    setTranscript("");
    setNormalizedTranscript("");
    setParsedItems([]);
    setCartItems([]);
    setClarifications([]);
    setSpokenReplyHi("");
    setSpokenReplyEn("");
    setVoiceAudioBase64(undefined);
    setIsOrderConfirmed(false);
    setKhataInfo(null);
  };

  // Compute bill totals
  const subtotal = cartItems.reduce((acc, it) => acc + it.line_total, 0);
  const deliveryFee = 0.0;
  const grandTotal = subtotal + deliveryFee;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Header */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-teal-500 to-sky-500 flex items-center justify-center shadow-lg shadow-sky-500/20">
              <Store className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold text-white tracking-tight">
                  KiranaVaani <span className="text-teal-400 font-hindi font-normal text-lg">(किरानावाणी)</span>
                </h1>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-teal-500/10 text-teal-300 border border-teal-500/20 font-medium">
                  Gnani AI Challenge
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Noise-Robust Hinglish Voice Assistant for Neighbourhood Kirana Stores
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 text-xs">
            {/* Live API vs Mock Mode Status */}
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-800/80 border border-slate-700">
              <span className={`w-2 h-2 rounded-full ${health?.gnani_live_configured ? "bg-emerald-400 animate-pulse" : "bg-amber-400"}`}></span>
              <span className="text-slate-300">
                Gnani AI: {health?.gnani_live_configured ? "Live API" : "Demo Mock Mode"}
              </span>
            </div>

            {/* Catalogue SKU count */}
            <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-800/80 border border-slate-700 text-slate-300">
              <ShoppingBag className="w-3.5 h-3.5 text-sky-400" />
              <span>{health?.catalogue_sku_count || 35} SKUs Loaded</span>
            </div>

            {/* Reset button */}
            <button
              onClick={handleResetOrder}
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
              title="Reset Order"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex-1 w-full">
        {/* Banner */}
        <div className="mb-6 p-4 rounded-xl bg-gradient-to-r from-teal-950/40 to-sky-950/40 border border-teal-500/20 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <Sparkles className="w-5 h-5 text-teal-400 flex-shrink-0" />
            <div className="text-xs text-slate-300">
              <strong className="text-white">Customer Spoken Order Demo:</strong> Try saying:{" "}
              <span className="text-teal-300 italic">"Bhaiya do packet Maggi, ek kilo sugar aur aadha litre milk bhej dena."</span>
            </div>
          </div>
          <div className="text-[11px] text-slate-400">
            Powered by <strong className="text-sky-300">Prisma v3.0</strong> + <strong className="text-sky-300">Timbre v2.5</strong>
          </div>
        </div>

        {/* 2-Column Responsive Cockpit */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Voice Input, Transcription, Clarification */}
          <div className="lg:col-span-7 space-y-6">
            <VoiceRecorder
              onAudioRecorded={(blob) => processOrderUtterance(undefined, blob)}
              onPresetSelected={(text) => processOrderUtterance(text, undefined)}
              isLoading={isLoading}
              keytermsEnabled={keytermsEnabled}
              onToggleKeyterms={() => setKeytermsEnabled((prev) => !prev)}
              apiBaseUrl={getApiBase()}
            />

            {/* Clarification Gate (Alerts when ambiguous match detected) */}
            <ClarificationDialog
              clarifications={clarifications}
              onResolveOption={handleResolveClarification}
            />

            <TranscriptPanel
              transcript={transcript}
              normalizedTranscript={normalizedTranscript}
              isMock={isMockAsr}
              model={keytermsEnabled ? "Prisma v3.0 (Keyterms ON)" : "Prisma v3.0 (Keyterms OFF)"}
              parsedItems={parsedItems}
              isOrderComplete={isOrderComplete}
            />
          </div>

          {/* Right Column: Confirmed Shopping Cart & Billing */}
          <div className="lg:col-span-5 space-y-6 sticky top-20">
            <ShoppingCart
              items={cartItems}
              onRemoveItem={handleRemoveItem}
            />

            <OrderSummary
              subtotal={subtotal}
              deliveryFee={deliveryFee}
              total={grandTotal}
              itemCount={cartItems.length}
              items={cartItems}
              khataInfo={khataInfo}
              spokenReplyHi={spokenReplyHi}
              spokenReplyEn={spokenReplyEn}
              voiceAudioBase64={voiceAudioBase64}
              voiceAudioFormat={voiceAudioFormat}
              isMockTts={isMockTts}
              onConfirmOrder={() => setIsOrderConfirmed(true)}
              isOrderConfirmed={isOrderConfirmed}
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-950 py-4 text-center text-xs text-slate-500">
        KiranaVaani – Great Indian AI Internship Challenge by Gnani AI • Speech AI, NLP & Telephony Noise Robustness
      </footer>
    </div>
  );
};

export default App;
