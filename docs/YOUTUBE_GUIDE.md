# KiranaVaani — YouTube Submission Guide & Video Kit

This kit contains all the assets, copy, timestamps, tags, and settings required to upload and submit the KiranaVaani Build Demo Video for the Gnani.ai Great Indian AI Internship Challenge.

Note: In accordance with YouTube Studio rules, this guide and copy-paste text contains zero angle brackets.

---

## 1. Quick File Reference

| Asset | Local File Path | Format / Size | Description |
| :--- | :--- | :--- | :--- |
| Demo Video (2:48) | [KiranaVaani_Build_Demo_2to3min.mp4](file:///D:/gnani%20challenge/KiranaVaani_Build_Demo_2to3min.mp4) | 1080p MP4 (4.81 MB) | Official 2m 48s build demo with synchronized neural voiceover and high-DPI slides. |
| Custom Thumbnail | [KiranaVaani_YouTube_Thumbnail.png](file:///D:/gnani%20challenge/KiranaVaani_YouTube_Thumbnail.png) | 1920x1080 PNG (956 KB) | High-CTR custom thumbnail with neon accents, speech bubble, and key metrics. |
| Architecture Slide | [kirana_vaani_system_architecture_slide.png](file:///D:/gnani%20challenge/kirana_vaani_system_architecture_slide.png) | 1920x1080 PNG (692 KB) | High-res 4-stage system architecture slide. |
| Benchmark Plot | [reports/ablation_benchmark_plot.png](file:///D:/gnani%20challenge/reports/ablation_benchmark_plot.png) | 2520x1080 PNG (157 KB) | Publication-grade WER vs. Item-F1 ablation benchmark curve. |

---

## 2. YouTube Video Titles (Choose One)

Option 1 (Recommended — Official and Clear):
KiranaVaani – Noise-Robust Hinglish Voice Assistant for Local Kirana Stores | Gnani.ai Challenge

Option 2 (Technical and Metric-Driven):
Building a Hinglish Voice AI Assistant for Noisy Kirana Stores (91.1% Item-F1 @ 0 dB Noise)

Option 3 (Compact and Catchy):
KiranaVaani: Voice AI for Bharat's Neighbourhood Retail | Powered by Gnani.ai

---

## 3. YouTube Video Description (Copy and Paste Ready)

KiranaVaani (किरानावाणी) is a noise-robust Hinglish voice assistant and telephony evaluation suite designed for Indian neighbourhood grocery (kirana) stores. Built for the Gnani.ai Great Indian AI Internship Challenge.

🛒 GitHub Repository: https://github.com/vikassharma270907-alt/kiranavaani
🎙️ Powered by: Gnani.ai Prisma v3.0 STT & Timbre v2.5 TTS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ CHAPTER TIMESTAMPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
0:00 - Introduction & Live Cockpit Overview
0:15 - 4-Stage System Architecture Pipeline
0:33 - Live Spoken Order Ingestion (Clip 1)
0:51 - 200 Catalog Keyterms Biasing (ASR Hardening)
1:07 - Colloquial Numeral Normalization ("सवा दो", "ढाई", "आधा")
1:24 - Active Clarification Loop (Clip 2: Basmati vs Sona Masoori)
1:42 - Running Cart & Gnani Timbre v2.5 Spoken Readback
1:59 - Telephony Noise Lab (5 Acoustic Tiers down to 0 dB SNR)
2:17 - Research Metrics: Why Item-F1 Trumps Raw WER
2:34 - Project Impact & Challenge Target Awards

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌟 KEY CAPABILITIES & INNOVATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Gnani Prisma v3.0 STT: Seamless Auto-LID (98.4% accuracy) detects code-mixed Hindi and English. Emits Hindi in Devanagari and brand names in Latin script.
2. 200 Catalog Keyterms Biasing: Injected into beam-search decoding, eliminating phonetic distortion (e.g. "meghee" to "Maggi", "kurkura" to "Kurkure").
3. Colloquial Indian Numeral Normalizer: Automatically maps colloquial fractions ("सवा दो किलो" to 2.25 kg, "ढाई किलो" to 2.5 kg, "आधा लीटर" to 0.5 L) across units.
4. Active Clarification Gate: If confidence falls below 0.78 (e.g. asking for "चावल" without specifying Basmati vs. Sona Masoori), the assistant triggers a conversational re-ask prompt instead of guessing.
5. Gnani Timbre v2.5 TTS: Context-aware Indian prosody with bilingual rupee currency pronunciation for natural order confirmation.
6. Telephony Noise Lab: Rigorous benchmark across ITU-T G.711 mu-law (8 kHz) companding and ESC-50 noise down to 0 dB market babble.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 RESEARCH BENCHMARK HIGHLIGHTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tested on an 80-utterance synthetic test set across 5 acoustic tiers:
• Tier 1: Clean Studio Mic (16 kHz, +30 dB): 91.07% Item-F1
• Tier 2: 8 kHz mu-Law Telephony (+20 dB): 91.07% Item-F1
• Tier 3: Shop Ceiling Fan (+10 dB, 8 kHz): 91.07% Item-F1
• Tier 4: Street Traffic Noise (+5 dB, 8 kHz): 91.07% Item-F1
• Tier 5: Crowded Market Babble (0 dB, 8 kHz): 84.6% to 91.07% Item-F1 (+25.2% recall lift over baseline!)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 TARGET AWARD CATEGORIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Mixed Vibes: Fluid Hinglish ingestion with Auto-LID and native code-mix mode.
• Real Deal: High-frequency phone orders with colloquial Indian fractional quantities.
• Noise Canceller: 8 kHz mu-law companding + ESC-50 noise resilience at 0 dB SNR.
• Demo Day Drop: Interactive cockpit with waveform visualizer and 2.8-minute demo video.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔒 DATA COMPLIANCE DECLARATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
All test audio, transcripts, phone numbers, and customer names are 100% synthetically generated. Zero real customer PII was used or collected.

#GnaniAI #GreatIndianAIInternshipChallenge #SpeechAI #VoiceAI #Hinglish #Kirana #MadeInIndia #VoiceCommerce

---

## 4. YouTube Video Tags (Copy and Paste into Video Tags Field)

Gnani AI, Great Indian AI Internship Challenge, KiranaVaani, Speech AI, Voice Assistant, Hinglish ASR, Prisma STT, Timbre TTS, Telephony Noise, ITU-T G.711, mu-law, ESC-50 noise, Item-level F1, WER, Speech to Text, Text to Speech, Indian Languages, Voice Commerce, Kirana Store, AI Hackathon

---

## 5. Recommended YouTube Upload Settings

* Visibility: Public (or Unlisted initially for verification)
* Category: Science & Technology
* Audience: No, it's not made for kids
* Video Language: English (India) / Hindi
* Captions: Upload transcript or use automatic English captions
* Recording Date: Current date
* License: Standard YouTube License
* Allow Embedding: Enabled
* Publish to Subscriptions Feed & Notify: Enabled

---

## 6. Thumbnail Upload Checklist

1. In YouTube Studio, navigate to Content and click on your uploaded video.
2. Under the Thumbnail section, click Upload thumbnail.
3. Select KiranaVaani_YouTube_Thumbnail.png (file:///D:/gnani%20challenge/KiranaVaani_YouTube_Thumbnail.png).
4. Verify that the thumbnail renders clearly with bold typography ("KIRANAVAANI", "91.1% Item-F1", "2.8 MIN DEMO").
5. Click Save.
