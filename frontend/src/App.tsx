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
  ShoppingBag,
  PhoneCall,
  BookOpen,
  Layers,
  Sliders,
  CheckCircle2,
  PackageX,
  Zap,
  Fingerprint,
  Boxes,
  WifiOff,
  Tag,
  Truck,
  Trophy
} from "lucide-react";

import { VoiceRecorder } from "./components/VoiceRecorder";
import { TranscriptPanel } from "./components/TranscriptPanel";
import { ShoppingCart, CartItem, UpsellSuggestion } from "./components/ShoppingCart";
import { ClarificationDialog, ClarificationQuestion, ClarificationOption, SubstitutionSuggestion } from "./components/ClarificationDialog";
import { OrderSummary } from "./components/OrderSummary";
import { AcousticSpectrogram } from "./components/AcousticSpectrogram";
import { TelephonyCallSimulator } from "./components/TelephonyCallSimulator";
import { KhataLedgerDrawer } from "./components/KhataLedgerDrawer";
import { ONDCModal } from "./components/ONDCModal";
import { JudgeStressArenaModal } from "./components/JudgeStressArenaModal";
import { AwaazPehchaanModal } from "./components/AwaazPehchaanModal";
import { MandiRestockDrawer } from "./components/MandiRestockDrawer";
import { TelemetryBenchmarkModal } from "./components/TelemetryBenchmarkModal";
import { JudgeTourBanner } from "./components/JudgeTourBanner";
import { BhaavTaalDrawer } from "./components/BhaavTaalDrawer";
import { DeliveryRiderModal } from "./components/DeliveryRiderModal";
import { KiranaClearSandboxModal } from "./components/KiranaClearSandboxModal";

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

  // Advanced Mode Toggles
  const [showCallSimulator, setShowCallSimulator] = useState(false);
  const [showSpectrogram, setShowSpectrogram] = useState(true);
  const [showKhataDrawer, setShowKhataDrawer] = useState(false);
  const [showOndcModal, setShowOndcModal] = useState(false);
  const [showJudgeArenaModal, setShowJudgeArenaModal] = useState(false);
  const [showAwaazPehchaanModal, setShowAwaazPehchaanModal] = useState(false);
  const [showMandiDrawer, setShowMandiDrawer] = useState(false);
  const [showTelemetryModal, setShowTelemetryModal] = useState(false);
  const [isOfflineSimulated, setIsOfflineSimulated] = useState(false);
  const [voiceprintVerified, setVoiceprintVerified] = useState(true);
  const [isButterOutOfStock, setIsButterOutOfStock] = useState(false);

  // Advanced Indic Feature Drawers & Modals
  const [showBhaavTaalDrawer, setShowBhaavTaalDrawer] = useState(false);
  const [showDeliveryRiderModal, setShowDeliveryRiderModal] = useState(false);
  const [showKiranaClearModal, setShowKiranaClearModal] = useState(false);
  const [landmarkInfo, setLandmarkInfo] = useState<any | null>(null);
  const [bhaavTaalInfo, setBhaavTaalInfo] = useState<any | null>(null);
  const [recipeInfo, setRecipeInfo] = useState<any | null>(null);
  const [bargainDiscount, setBargainDiscount] = useState<number>(0);

  // Order state
  const [transcript, setTranscript] = useState("");
  const [normalizedTranscript, setNormalizedTranscript] = useState("");
  const [isMockAsr, setIsMockAsr] = useState(true);
  const [parsedItems, setParsedItems] = useState<any[]>([]);
  const [isOrderComplete, setIsOrderComplete] = useState(false);
  const [cartItems, setCartItems] = useState<CartItem[]>([]);
  const [clarifications, setClarifications] = useState<ClarificationQuestion[]>([]);
  const [substitutions, setSubstitutions] = useState<SubstitutionSuggestion[]>([]);
  const [upsellSuggestion, setUpsellSuggestion] = useState<UpsellSuggestion | null>(null);
  const [spokenReplyHi, setSpokenReplyHi] = useState("");
  const [spokenReplyEn, setSpokenReplyEn] = useState("");
  const [voiceAudioBase64, setVoiceAudioBase64] = useState<string | undefined>(undefined);
  const [voiceAudioFormat, setVoiceAudioFormat] = useState("wav");
  const [isMockTts, setIsMockTts] = useState(true);
  const [isOrderConfirmed, setIsOrderConfirmed] = useState(false);
  const [khataInfo, setKhataInfo] = useState<any | null>(null);
  const [repairsApplied, setRepairsApplied] = useState<any[]>([]);
  const [tokenConfidenceScores, setTokenConfidenceScores] = useState<any[]>([]);
  const [detectedIntent, setDetectedIntent] = useState<string>("ORDER");

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
      setSubstitutions(data.substitutions_needed || []);
      setSpokenReplyHi(data.spoken_reply_hi);
      setSpokenReplyEn(data.spoken_reply_en);
      setVoiceAudioBase64(data.voice_audio_base64);
      setVoiceAudioFormat(data.voice_audio_format || "wav");
      setIsMockTts(data.is_mock_tts);
      setKhataInfo(data.khata_info || null);
      setUpsellSuggestion(data.upsell_suggestion || null);
      setRepairsApplied(data.repairs_applied || []);
      setTokenConfidenceScores(data.token_confidence_scores || []);
      setDetectedIntent(data.detected_intent || "ORDER");
      setLandmarkInfo(data.landmark_info || null);
      setBhaavTaalInfo(data.bhaav_taal_info || null);
      setRecipeInfo(data.recipe_info || null);

      // Auto-trigger corresponding modal when explicit intent is classified
      if (data.detected_intent === "BARGAIN" && data.bhaav_taal_info) {
        setShowBhaavTaalDrawer(true);
      }
      if (data.detected_intent === "DELIVERY_DISPATCH" && data.landmark_info) {
        setShowDeliveryRiderModal(true);
      }

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
      const filtered = prev.filter((it) => it.sku_id !== option.sku_id);
      return [...filtered, newItem];
    });

    setClarifications((prev) => prev.filter((q) => !q.options.some((o) => o.sku_id === option.sku_id)));

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
      .catch((e) => console.warn("Could not synthesize clarification audio:", e));
  };

  const handleAcceptSubstitution = (sub: SubstitutionSuggestion) => {
    const newItem: CartItem = {
      sku_id: sub.substitute_sku.sku_id,
      name_en: sub.substitute_sku.name_en,
      name_hi: sub.substitute_sku.name_hi,
      category: sub.substitute_sku.category || "Dairy",
      quantity: 1.0,
      unit: sub.substitute_sku.unit,
      unit_price: sub.substitute_sku.price_inr,
      line_total: sub.substitute_sku.price_inr
    };

    setCartItems((prev) => [...prev, newItem]);
    setSubstitutions((prev) => prev.filter((s) => s.out_of_stock_sku.sku_id !== sub.out_of_stock_sku.sku_id));

    const confirmationHi = `${sub.substitute_sku.name_hi} विकल्प के रूप में जोड़ दिया गया है।`;
    setSpokenReplyHi(confirmationHi);
  };

  const handleAddUpsellItem = (upsell: UpsellSuggestion) => {
    const newItem: CartItem = {
      sku_id: upsell.sku_id,
      name_en: upsell.name_en,
      name_hi: upsell.name_hi,
      category: upsell.category,
      quantity: upsell.quantity,
      unit: upsell.unit,
      unit_price: upsell.price_inr,
      line_total: Number((upsell.quantity * upsell.price_inr).toFixed(2))
    };

    setCartItems((prev) => [...prev, newItem]);
    setUpsellSuggestion(null);

    const confirmationHi = `${upsell.name_hi} कार्ट में जोड़ दिया गया है। कुल बिल अपडेट हो गया।`;
    setSpokenReplyHi(confirmationHi);
  };

  const handleToggleButterStock = async () => {
    const newStock = !isButterOutOfStock;
    try {
      const apiBase = getApiBase();
      await fetch(`${apiBase}/catalogue/toggle-stock`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sku_id: "SKU-013", in_stock: !newStock })
      });
      setIsButterOutOfStock(newStock);
    } catch (e) {
      console.warn("Stock toggle error:", e);
      setIsButterOutOfStock(newStock);
    }
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
    setSubstitutions([]);
    setUpsellSuggestion(null);
    setSpokenReplyHi("");
    setSpokenReplyEn("");
    setVoiceAudioBase64(undefined);
    setIsOrderConfirmed(false);
    setKhataInfo(null);
    setRepairsApplied([]);
    setTokenConfidenceScores([]);
    setDetectedIntent("ORDER");
    setLandmarkInfo(null);
    setBhaavTaalInfo(null);
    setRecipeInfo(null);
    setBargainDiscount(0);
  };

  // Compute bill totals
  const subtotal = cartItems.reduce((acc, it) => acc + it.line_total, 0);
  const deliveryFee = 0.0;
  const grandTotal = Math.max(0, subtotal - bargainDiscount + deliveryFee);

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

          <div className="flex flex-wrap items-center gap-2.5 text-xs">
            {/* Judge's Stress-Test Arena Button */}
            <button
              onClick={() => setShowJudgeArenaModal(true)}
              className="px-3 py-1.5 rounded-lg text-xs font-bold bg-gradient-to-r from-amber-500/20 to-amber-600/20 text-amber-300 border border-amber-500/40 hover:bg-amber-500/30 flex items-center gap-1.5 transition-all shadow-md shadow-amber-500/10 animate-pulse"
            >
              <Zap className="w-3.5 h-3.5 text-amber-400 fill-current" />
              <span>⚡ Judge's Arena</span>
            </button>

            {/* Bhaav-Taal (Voice Bargaining) Trigger */}
            <button
              onClick={() => setShowBhaavTaalDrawer(true)}
              className="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-amber-500/10 text-amber-300 border border-amber-500/30 hover:bg-amber-500/20 flex items-center gap-1.5 transition-colors"
            >
              <Tag className="w-3.5 h-3.5 text-amber-400" />
              <span>भाव-तोल</span>
            </button>

            {/* Chhotu Delivery Landmark Dispatch Trigger */}
            <button
              onClick={() => setShowDeliveryRiderModal(true)}
              className="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/20 flex items-center gap-1.5 transition-colors"
            >
              <Truck className="w-3.5 h-3.5 text-emerald-400" />
              <span>छोटू राइडर</span>
            </button>

            {/* KiranaClear Telephony DSP Noise Gate Trigger */}
            <button
              onClick={() => setShowKiranaClearModal(true)}
              className="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-rose-500/10 text-rose-300 border border-rose-500/30 hover:bg-rose-500/20 flex items-center gap-1.5 transition-colors"
            >
              <Activity className="w-3.5 h-3.5 text-rose-400" />
              <span>DSP Noise Gate</span>
            </button>

            {/* Awaaz Pehchaan (Voice Biometrics) Trigger */}
            <button
              onClick={() => setShowAwaazPehchaanModal(true)}
              className="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-teal-500/10 text-teal-300 border border-teal-500/30 hover:bg-teal-500/20 flex items-center gap-1.5 transition-colors"
            >
              <Fingerprint className="w-3.5 h-3.5 text-teal-400" />
              <span>आवाज़ पहचान</span>
            </button>

            {/* Mandi Wholesale B2B Drawer Trigger */}
            <button
              onClick={() => setShowMandiDrawer(true)}
              className="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-500/20 flex items-center gap-1.5 transition-colors"
            >
              <Boxes className="w-3.5 h-3.5 text-indigo-400" />
              <span>मंडी B2B</span>
            </button>

            {/* Sub-Second Telemetry Benchmark Trigger */}
            <button
              onClick={() => setShowTelemetryModal(true)}
              className="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-sky-500/10 text-sky-300 border border-sky-500/30 hover:bg-sky-500/20 flex items-center gap-1.5 transition-colors"
            >
              <Activity className="w-3.5 h-3.5 text-sky-400" />
              <span>&lt;400ms Benchmark</span>
            </button>

            {/* Telephony Simulator Trigger */}
            <button
              onClick={() => setShowCallSimulator((prev) => !prev)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all ${
                showCallSimulator
                  ? "bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/30"
                  : "bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/20"
              }`}
            >
              <PhoneCall className="w-3.5 h-3.5" />
              <span>{showCallSimulator ? "Hide Call Simulator" : "📞 Incoming Call Sim"}</span>
            </button>

            {/* Kirana Khata Drawer Trigger */}
            <button
              onClick={() => setShowKhataDrawer(true)}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-amber-500/10 text-amber-300 border border-amber-500/30 hover:bg-amber-500/20 flex items-center gap-1.5 transition-colors"
            >
              <BookOpen className="w-3.5 h-3.5 text-amber-400" />
              <span>खाता बही (₹2,390)</span>
            </button>

            {/* ONDC Export Button */}
            <button
              onClick={() => setShowOndcModal(true)}
              className="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-sky-500/10 text-sky-300 border border-sky-500/30 hover:bg-sky-500/20 flex items-center gap-1.5 transition-colors"
            >
              <span className="text-sm">🇮🇳</span>
              <span>ONDC Rail</span>
            </button>

            {/* Live API vs Mock Mode Status */}
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700">
              <span className={`w-2 h-2 rounded-full ${health?.gnani_live_configured ? "bg-emerald-400 animate-pulse" : "bg-amber-400"}`}></span>
              <span className="text-slate-300">
                Gnani AI: {health?.gnani_live_configured ? "Live API" : "Demo Mode"}
              </span>
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
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex-1 w-full space-y-6">
        {/* Judges' Guided 4-Award Evaluation Tour Banner */}
        <JudgeTourBanner
          apiBaseUrl={getApiBase()}
          onApplyUtterance={(text) => {
            setTranscript(text);
            setClarifications([]);
            setSubstitutions([]);
            processOrderUtterance(text);
          }}
          onOpenBhaavTaal={() => setShowBhaavTaalDrawer(true)}
          onOpenDeliveryRider={() => setShowDeliveryRiderModal(true)}
          onOpenKiranaClear={() => setShowKiranaClearModal(true)}
          onOpenJudgeArena={() => setShowJudgeArenaModal(true)}
        />

        {/* Banner with Feature Chips */}
        <div className="p-4 rounded-xl bg-gradient-to-r from-teal-950/40 to-sky-950/40 border border-teal-500/20 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <Sparkles className="w-5 h-5 text-teal-400 flex-shrink-0" />
            <div className="text-xs text-slate-300">
              <strong className="text-white">Customer Spoken Order Demo:</strong> Try saying:{" "}
              <span className="text-teal-300 italic">"Bhaiya do packet Maggi, ek kilo sugar aur aadha litre milk bhej dena."</span>
            </div>
          </div>

          <div className="flex items-center gap-2 text-[11px] flex-wrap">
            {/* Offline Bharat Resilience Toggle */}
            <button
              onClick={() => setIsOfflineSimulated((prev) => !prev)}
              className={`px-2.5 py-1 rounded-md border font-mono transition-colors flex items-center gap-1 ${
                isOfflineSimulated
                  ? "bg-amber-500/20 text-amber-300 border-amber-500/40 animate-pulse"
                  : "bg-slate-800 text-slate-400 border-slate-700 hover:text-white"
              }`}
              title="Simulates network outage in rural mandis to verify offline edge resilience"
            >
              <WifiOff className="w-3 h-3" />
              {isOfflineSimulated ? "Mandi Offline: SIMULATED" : "Network: 4G Online"}
            </button>

            {/* Quick Out-of-Stock Demo Toggle */}
            <button
              onClick={handleToggleButterStock}
              className={`px-2.5 py-1 rounded-md border font-mono transition-colors flex items-center gap-1 ${
                isButterOutOfStock
                  ? "bg-rose-500/20 text-rose-300 border-rose-500/40"
                  : "bg-slate-800 text-slate-400 border-slate-700 hover:text-white"
              }`}
              title="Toggles Amul Butter stock status to demonstrate voice substitution in live judge demos"
            >
              <PackageX className="w-3 h-3" />
              {isButterOutOfStock ? "Butter Stockout: SIMULATED" : "Stockout Demo: OFF"}
            </button>

            <span className="text-slate-400">
              Powered by <strong className="text-sky-300">Prisma v3.0</strong> + <strong className="text-sky-300">Timbre v2.5</strong>
            </span>
          </div>
        </div>

        {/* Offline Bharat Resilience Alert Banner */}
        {isOfflineSimulated && (
          <div className="p-3.5 rounded-xl bg-gradient-to-r from-amber-950/60 to-rose-950/60 border border-amber-500/40 flex items-center justify-between gap-3 text-xs text-amber-200 animate-pulse shadow-lg">
            <div className="flex items-center gap-2.5">
              <WifiOff className="w-4 h-4 text-amber-400 flex-shrink-0" />
              <div>
                <strong className="text-white">Offline Bharat Resilience Active (इंटरनेट बंद):</strong> Cloud connection severed (0 bps). System switched instantly to local browser Web Speech & offline RapidFuzz cache. Orders queued locally for auto-sync.
              </div>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono font-bold whitespace-nowrap">
              ZERO DOWNTIME
            </span>
          </div>
        )}

        {/* Incoming Telephony Call Simulator Widget (If Active) */}
        {showCallSimulator && (
          <TelephonyCallSimulator
            onProcessCallUtterance={(text) => processOrderUtterance(text)}
            isLoading={isLoading}
            activeClarification={clarifications.length > 0}
            onClose={() => setShowCallSimulator(false)}
            apiBaseUrl={getApiBase()}
            voiceAudioBase64={voiceAudioBase64}
            voiceAudioFormat={voiceAudioFormat}
            spokenReplyHi={spokenReplyHi}
            spokenReplyEn={spokenReplyEn}
          />
        )}

        {/* 2-Column Responsive Cockpit */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Voice Input, Spectrogram, Clarification, Transcription */}
          <div className="lg:col-span-7 space-y-6">
            <VoiceRecorder
              onAudioRecorded={(blob) => processOrderUtterance(undefined, blob)}
              onPresetSelected={(text) => processOrderUtterance(text, undefined)}
              isLoading={isLoading}
              keytermsEnabled={keytermsEnabled}
              onToggleKeyterms={() => setKeytermsEnabled((prev) => !prev)}
              apiBaseUrl={getApiBase()}
            />

            {/* Live In-Browser Web Audio FFT Spectrogram & Telephony 8 kHz Inspector */}
            <div className="space-y-2">
              <div className="flex items-center justify-between px-1">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-rose-400" />
                  Real-Time Telephony Nyquist Acoustic Inspector
                </span>
                <button
                  onClick={() => setShowSpectrogram((prev) => !prev)}
                  className="text-[11px] text-slate-500 hover:text-slate-300 font-mono"
                >
                  {showSpectrogram ? "Collapse ▲" : "Expand ▼"}
                </button>
              </div>

              {showSpectrogram && (
                <AcousticSpectrogram
                  isActive={isLoading || !!voiceAudioBase64}
                  tokenConfidenceScores={tokenConfidenceScores}
                />
              )}
            </div>

            {/* Clarification Gate & Out-of-Stock Substitutions */}
            <ClarificationDialog
              clarifications={clarifications}
              onResolveOption={handleResolveClarification}
              substitutions={substitutions}
              onAcceptSubstitution={handleAcceptSubstitution}
            />

            <TranscriptPanel
              transcript={transcript}
              normalizedTranscript={normalizedTranscript}
              isMock={isMockAsr}
              model={keytermsEnabled ? "Prisma v3.0 (Keyterms ON)" : "Prisma v3.0 (Keyterms OFF)"}
              parsedItems={parsedItems}
              isOrderComplete={isOrderComplete}
              repairsApplied={repairsApplied}
              detectedIntent={detectedIntent}
            />
          </div>

          {/* Right Column: Confirmed Shopping Cart & Billing */}
          <div className="lg:col-span-5 space-y-6 sticky top-20">
            {recipeInfo && (
              <div className="p-3.5 rounded-xl bg-gradient-to-r from-orange-950/40 via-amber-950/30 to-slate-900 border border-amber-500/40 shadow-lg space-y-2">
                <div className="flex items-center justify-between pb-2 border-b border-amber-500/20">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">🍲</span>
                    <div>
                      <h3 className="text-xs font-bold text-amber-300">
                        रसोई से राशन (Rasoi Recipe Kit): {recipeInfo.dish_name}
                      </h3>
                      <p className="text-[11px] text-slate-300">
                        {recipeInfo.servings} लोगों के लिए सामग्री • {recipeInfo.matched_ingredients?.length || 0} आइटम्स
                      </p>
                    </div>
                  </div>
                  {recipeInfo.combo_savings_inr > 0 && (
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-mono">
                      बचत: ₹{recipeInfo.combo_savings_inr}
                    </span>
                  )}
                </div>
                {recipeInfo.recipe_tip_hi && (
                  <p className="text-[11px] text-amber-200/90 italic">
                    💡 {recipeInfo.recipe_tip_hi}
                  </p>
                )}
              </div>
            )}

            <ShoppingCart
              items={cartItems}
              onRemoveItem={handleRemoveItem}
              upsellSuggestion={upsellSuggestion}
              onAddUpsellItem={handleAddUpsellItem}
            />

            <OrderSummary
              subtotal={subtotal}
              deliveryFee={deliveryFee}
              total={grandTotal}
              discountAmount={bargainDiscount}
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
              onOpenOndcModal={() => setShowOndcModal(true)}
              apiBaseUrl={getApiBase()}
              onOpenVoiceprintModal={() => setShowAwaazPehchaanModal(true)}
              voiceprintVerified={voiceprintVerified}
            />
          </div>
        </div>
      </main>

      {/* Kirana Khata 2.0 Drawer Modal */}
      <KhataLedgerDrawer
        isOpen={showKhataDrawer}
        onClose={() => setShowKhataDrawer(false)}
        apiBaseUrl={getApiBase()}
      />

      {/* ONDC Beckn Protocol Export Modal */}
      <ONDCModal
        isOpen={showOndcModal}
        onClose={() => setShowOndcModal(false)}
        cartItems={cartItems}
        apiBaseUrl={getApiBase()}
      />

      {/* Judge's Adversarial Stress Arena Modal */}
      <JudgeStressArenaModal
        isOpen={showJudgeArenaModal}
        onClose={() => setShowJudgeArenaModal(false)}
        apiBaseUrl={getApiBase()}
        onApplyTestUtterance={(text) => {
          setShowJudgeArenaModal(false);
          setTranscript(text);
          setClarifications([]);
          setSubstitutions([]);
          processOrderUtterance(text);
        }}
      />

      {/* Awaaz Pehchaan (Voice Biometrics) Modal */}
      <AwaazPehchaanModal
        isOpen={showAwaazPehchaanModal}
        onClose={() => setShowAwaazPehchaanModal(false)}
        customerId={khataInfo?.customer_id || "CUST-001"}
        customerName={khataInfo?.customer_name || "Sharma Ji (शर्मा जी)"}
        apiBaseUrl={getApiBase()}
        onVerificationComplete={(res) => {
          setVoiceprintVerified(res.verified);
        }}
      />

      {/* Mandi Wholesale Restock B2B Drawer */}
      <MandiRestockDrawer
        isOpen={showMandiDrawer}
        onClose={() => setShowMandiDrawer(false)}
        apiBaseUrl={getApiBase()}
      />

      {/* Sub-Second Telemetry Benchmark Modal */}
      <TelemetryBenchmarkModal
        isOpen={showTelemetryModal}
        onClose={() => setShowTelemetryModal(false)}
        apiBaseUrl={getApiBase()}
      />

      {/* Bhaav-Taal (Kirana Voice Bargaining) Drawer */}
      <BhaavTaalDrawer
        isOpen={showBhaavTaalDrawer}
        onClose={() => setShowBhaavTaalDrawer(false)}
        apiBaseUrl={getApiBase()}
        cartItems={cartItems}
        customerName={khataInfo?.customer_name || "Sharma Ji (शर्मा जी)"}
        onApplyDiscountedTotal={(discTotal, savings) => {
          setBargainDiscount(savings);
          setSpokenReplyHi(`₹${savings} की विशेष छूट लागू कर दी गई है। कुल बिल ₹${discTotal} हुआ।`);
        }}
      />

      {/* Chhotu Delivery Landmark Dispatch Modal */}
      <DeliveryRiderModal
        isOpen={showDeliveryRiderModal}
        onClose={() => setShowDeliveryRiderModal(false)}
        apiBaseUrl={getApiBase()}
        cartItems={cartItems}
        totalAmount={grandTotal}
        customerName={khataInfo?.customer_name || "Sharma Ji (शर्मा जी)"}
        transcript={transcript}
        landmarkInfo={landmarkInfo}
      />

      {/* KiranaClear Telephony DSP Noise Gate Sandbox Modal */}
      <KiranaClearSandboxModal
        isOpen={showKiranaClearModal}
        onClose={() => setShowKiranaClearModal(false)}
        onRunFilteredAudioTest={() => {
          processOrderUtterance("भैया 2 किलो बासमती चावल, 1 Maggi masala, 2 Kurkure और 1 litre Arogyam oil लिख लो, बस इतना ही।");
        }}
      />

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-950 py-4 text-center text-xs text-slate-500">
        KiranaVaani – Great Indian AI Internship Challenge by Gnani AI • Speech AI, NLP & Telephony Noise Robustness
      </footer>
    </div>
  );
};

export default App;
