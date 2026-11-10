# KiranaVaani — Technical Architecture Specification

This document details the software architecture, speech processing pipeline, conversational state machine, and data flow of **KiranaVaani**.

---

## 1. High-Level System Architecture

```mermaid
flowchart TD
    subgraph Client ["Client Layer (Frontend)"]
        UI[React 18 + Vite Cockpit]
        MIC[Browser MediaRecorder / Audio Input]
        AUDIO_OUT[Web Audio Player / Chime Player]
    end

    subgraph Channel ["Acoustic & Telephony Simulation"]
        RESAMP[8 kHz Bandpass Resampler\n300 Hz - 3400 Hz]
        CODEC[ITU-T G.711 μ-Law Codec\n8-bit Logarithmic Companding]
        NOISE[Acoustic Noise Injection\n20dB, 10dB, 5dB, 0dB SNR]
    end

    subgraph Speech_AI ["Gnani.ai Speech Engines"]
        PRISMA[Gnani Prisma v3.0 STT\nAuto-LID 98.4% + Code-Mix]
        KEYTERMS[(200 Kirana Catalog Keyterms\nBeam Search Biasing)]
        TIMBRE[Gnani Timbre v2.5 TTS\nIndian Prosody & Hindi-IN]
    end

    subgraph Backend_Core ["FastAPI Backend Pipeline"]
        PARSER[Hinglish Order Parser\nNumeral Normalizer & Clause Splitter]
        MATCHER{RapidFuzz Matcher &\nAmbiguity Gate}
        CATALOG[(Kirana Catalogue\n35 Multilingual SKUs)]
        CART[Shopping Cart & Billing Engine]
    end

    MIC --> UI
    UI -->|REST / Multipart WAV| PRISMA
    KEYTERMS -.->|Bias Beam Search| PRISMA
    PRISMA -->|Code-Mixed Transcript| PARSER
    PARSER -->|Normalized Items & Qty| MATCHER
    CATALOG --- MATCHER
    MATCHER -->|Confidence >= 0.78 & Unambiguous| CART
    MATCHER -->|Ambiguous / Confidence < 0.78| UI
    CART -->|Spoken Readback Text| TIMBRE
    TIMBRE -->|WAV Audio Base64| AUDIO_OUT

    classDef accent fill:#0284c7,stroke:#0369a1,color:#fff;
    classDef engine fill:#0f766e,stroke:#115e59,color:#fff;
    class PRISMA,TIMBRE engine;
    class PARSER,MATCHER,CART accent;
```

---

## 2. End-to-End Execution Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Caller as Customer / Caller
    participant UI as KiranaVaani Cockpit
    participant API as FastAPI Backend (/process-order)
    participant STT as Gnani Prisma v3.0 STT
    participant NLP as Hinglish Order Parser
    participant Matcher as Catalogue Matcher
    participant Cart as Cart Service
    participant TTS as Gnani Timbre v2.5 TTS

    Caller->>UI: Speaks order ("दो पैकेट मैगी, एक किलो sugar और आधा litre milk")
    UI->>API: POST /process-order (audio or transcript)
    
    alt Audio Provided
        API->>STT: POST /stt/v3 (with 200 keyterms)
        STT-->>API: Returns transcript ("Bhaiya do packet Maggi, ek kilo sugar...")
    end

    API->>NLP: parse_utterance(transcript)
    Note over NLP: Normalizes "do"->2, "ek"->1, "aadha"->0.5<br/>Strips fillers ("Bhaiya", "bhej dena")
    NLP-->>API: Extracted items: [Maggi: 2 pkt, Sugar: 1 kg, Milk: 0.5 L]

    API->>Matcher: match_items(items)
    Note over Matcher: Matches Sugar -> SKU-020 (Madhur Sugar)<br/>Matches Milk -> SKU-012 (Amul Milk)<br/>Detects Maggi Ambiguity (Masala vs Atta)
    
    Matcher-->>API: Confirmed: [Sugar, Milk]<br/>Clarification Needed: [Maggi]

    API->>Cart: build_cart([Sugar, Milk])
    Cart-->>API: Subtotal: ₹60.00, Total: ₹60.00

    API->>TTS: POST /api/v1/tts/inference (Spoken Clarification)
    TTS-->>API: Synthesized voice audio bytes
    
    API-->>UI: Return ProcessOrderResponse (Cart + Clarification Prompt + Audio)
    UI->>Caller: Displays cart & Plays spoken clarification: "'मैगी 2-मिनट मसाला' चाहिए या 'मैगी आटा'?"
    
    Caller->>UI: Clicks "मैगी २-मिनट मसाला (₹14)"
    UI->>API: POST /cart (Update with SKU-027)
    API-->>UI: Updated Cart: 3 items, Total ₹88.00
```

---

## 3. Core Subsystems

### 3.1. Telephony Channel & Acoustic Noise Injection
- **Resampling**: Standardizes input to 8 kHz sampling rate with a 4th-order Butterworth bandpass filter (300 Hz – 3400 Hz).
- **ITU-T G.711 $\mu$-law**: Compresses input with 8-bit non-linear quantization ($\mu = 255$).
- **Noise Injection**: Injects calibrated additive noise at +30 dB, +20 dB, +10 dB, +5 dB, and 0 dB SNR based on RMS power ratio:
  $$\alpha = \sqrt{\frac{P_{\text{speech}}}{P_{\text{noise}} \cdot 10^{\text{SNR}/10}}}$$

### 3.2. Hinglish Order Parser
- **Boundary-Safe Numeral Replacement**: Replaces multi-word fractional phrases (*"सवा दो"*, *"पौने दो"*, *"साढ़े तीन"*, *"पाव भर"*) before matching single-word numerals (*"ढाई"*, *"डेढ़"*, *"आधा"*).
- **Regex Boundary Lookarounds**: Uses `(?<![\w\u0900-\u097F])` and `(?![\w\u0900-\u097F])` to ensure Hindi characters are not broken midway through a ligature.
- **Unit Normalization**: Standardizes `kilo`, `kg`, `किलो` to `kg`, and converts `500 gram` to `0.5 kg` when the catalog unit is `kg`.

### 3.3. Catalogue Matcher & Ambiguity Gate
- **Family Ambiguity Resolvers**: Detects generic base nouns (*"chawal"*, *"dal"*, *"tel"*, *"maggi"*) that have multiple distinct SKU variants in store.
- **Score Delta Check**: If the similarity difference between candidate 1 and candidate 2 is $< 0.12$ and score is $< 0.92$, the matcher refuses to guess and emits a `ClarificationQuestion`.
- **Confidence Threshold**: Any candidate scoring below $0.78$ triggers a confirmation query rather than silent addition to the cart.

### 3.4. Gnani AI Timbre Speech Generation
- Formats synthesized spoken readbacks in colloquial Hindi/Hinglish.
- Generates natural phonetic pauses and summary cadence (*"Aapke order me 2 packet Maggi... kul 106 rupaye"*).
- Includes graceful zero-dependency fallback WAV synthesis when deployed without live cloud keys.
