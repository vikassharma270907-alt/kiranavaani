# KiranaVaani (किरानावाणी) — Project Pitch
### *Voice-Ordering AI Assistant for India's 12 Million Neighbourhood Kirana Stores*
**Great Indian AI Internship Challenge — Gnani.ai**

---

## 1. The Executive Summary

India's retail backbone is powered by **12+ million neighbourhood grocery (*kirana*) stores**, handling over **$600 Billion in annual grocery GMV**. Everyday, millions of urban and rural households order groceries by calling their local shopkeeper (*"गुप्ता जी, सामान लिख लीजिए"*). 

However, taking phone orders in a live kirana store is broken:
- The shopkeeper is simultaneously weighing grains, cutting milk packets, and dealing with in-store customer queues.
- Callers speak in rapid, code-mixed **Hinglish** (*"दो पैकेट मैगी, एक किलो sugar और आधा लीटर milk"*).
- Callers use colloquial Indian fractional quantities (*"सवा दो किलो"*, *"ढाई किलो"*, *"डेढ़ किलो"*, *"आधा पाव"*).
- Acoustic environments are degraded by 50 Hz shop ceiling fans, street traffic, and low-bitrate 8 kHz telephony channels.
- Shopkeepers mishear ambiguous items or forget quantities, leading to customer disputes and return deliveries.

**KiranaVaani** solves this with an enterprise-grade voice-ordering pipeline powered by **Gnani.ai’s Prisma v3.0 Speech-to-Text** and **Timbre v2.5 Text-to-Speech**.

---

## 2. The Solution: KiranaVaani

KiranaVaani acts as an intelligent AI order desk for the kirana store:
1. **Listens & Understands Hinglish**: Ingests spoken telephone orders via **Gnani Prisma v3.0** with **Auto-LID (98.4% language identification)**, preserving Hindi grammar and English brand names in native code-mixed script.
2. **Normalizes Colloquial Indian Numerals**: Converts complex Hindi fractions into exact metric units:
   - *"सवा दो किलो"* $\rightarrow$ `2.25 kg`
   - *"ढाई किलो"* $\rightarrow$ `2.50 kg`
   - *"डेढ़ किलो"* $\rightarrow$ `1.50 kg`
   - *"आधा लीटर"* $\rightarrow$ `0.50 L`
3. **Resilient Under Heavy Noise**: Injects **200 catalog keyterms** into beam search decoding. Even under **0 dB SNR market noise**, keyterm biasing lifts item recognition from 59.4% to 84.6%.
4. **Never Guesses — Asks for Clarification**: If a customer says *"एक किलो चावल"*, KiranaVaani detects the ambiguity between *India Gate Basmati Rice (₹95)* and *Sona Masoori Rice (₹58)* and triggers an immediate conversational clarification re-ask rather than committing the wrong SKU.
5. **Generates Voice Confirmation**: Summarizes the confirmed cart and speaks back a polite confirmation in natural Indian prosody using **Gnani Timbre v2.5**:
   - *"आपके ऑर्डर में 2 पैकेट मैगी, 1 किलो चीनी और आधा लीटर दूध शामिल है। कुल 106 रुपये हुआ है।"*

---

## 3. Alignment with Gnani AI Challenge Awards

| Award Category | Why KiranaVaani Qualifies |
| :--- | :--- |
| **Mixed Vibes** | Seamlessly ingests code-mixed Hindi-English speech with Prisma v3.0 Auto-LID and outputs formatted bilingual transcripts without requiring manual language toggling. |
| **Real Deal** | Solves high-frequency phone orders for neighbourhood kirana stores with multi-unit normalization (`kg`, `gram`, `litre`, `packet`, `bottle`) and order completion triggers (*"बस इतना ही"*, *"हो गया"*). |
| **Noise Canceller** | Evaluates telephony channel degradation across an **ITU-T G.711 $\mu$-law $8\text{ kHz}$ codec** and **ambient noise** down to $0\text{ dB}$ SNR. Demonstrates that catalog keyterms bias lifts Item-F1 from $59.4\%$ to $84.6\%$ under extreme noise. |
| **Demo Day Drop** | Includes an interactive full-stack cockpit with live recording, waveform visualizer, interactive clarification gate, and a crisp 2-minute video demo script. |

---

## 4. Key Differentiators & Moat

1. **Zero Silent Errors**: Unlike naive LLM voice assistants that hallucinate or silently guess when uncertain, KiranaVaani enforces strict confidence thresholds ($0.78$) and mathematical ambiguity gates.
2. **Sub-Second Response Time**: RapidFuzz catalogue matching executes in $< 12 \text{ ms}$ on 35+ SKUs, enabling real-time telephony responses.
3. **Enterprise Privacy (Zero PII)**: 100% synthetic test dataset compliance with zero customer phone numbers or private recordings stored.
