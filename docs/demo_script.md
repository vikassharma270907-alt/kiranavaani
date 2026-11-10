# KiranaVaani — 2-Minute Video Demonstration Script
### *Great Indian AI Internship Challenge — Gnani.ai*

**Video Target Duration**: 2 minutes 30 seconds  
**Presenter**: Engineering Intern Candidate  
**Tags**: `#GnaniAI #GreatIndianAIInternshipChallenge #SpeechAI #KiranaVaani #HinglishASR`

---

## Video Timeline & Script

### 0:00 – 0:25 | Hook & The Problem
**Visual**: Show KiranaVaani Cockpit UI with clean dark mode theme. Camera on presenter.
**Spoken Script**:
> "Namaste! In India, over 12 million neighbourhood kirana stores handle $600 billion in grocery sales. Everyday, customers call their local shopkeeper to order groceries. 
> But taking phone orders in a busy shop is chaotic. The shopkeeper is weighing grains or cutting milk packets, customers speak in rapid code-mixed Hinglish, use colloquial fractions like *'dhai kilo'* or *'aadha litre'*, and loud ceiling fans create heavy background noise.
> Meet **KiranaVaani** — a noise-robust voice assistant powered by **Gnani.ai’s Prisma v3.0** and **Timbre v2.5**."

---

### 0:25 – 0:55 | Live Hinglish Voice Order & Numeral Normalization
**Visual**: Presenter clicks the Microphone button. Waveform pulsates.
**Spoken Order**:
> *"Bhaiya, do packet Maggi, ek kilo sugar aur aadha litre milk bhej dena."*

**Visual**: Presenter clicks Stop. The transcription appears in under a second:
- Auto-LID badge highlights: `hi-Latn / hi-Deva (Code-Mixed)`
- Normalized representation highlights: `2 packet Maggi`, `1 kg Sugar`, `0.5 litre Milk`.
- Cart updates with Sugar (₹45) and Milk (₹16.50).

**Presenter Voiceover**:
> "Notice what happened in sub-second latency: Gnani Prisma v3.0 detected the code-mixed language automatically. Our Hinglish order parser normalized *'do'* into `2`, *'ek kilo'* into `1 kg`, and the colloquial fraction *'aadha litre'* into `0.5 L`."

---

### 0:55 – 1:25 | The Ambiguity Gate (Never Guess Wrong!)
**Visual**: Camera zooms in on the amber **Clarification Required** card.
**Visual**: The system asks:
> *"मैगी 2-मिनट मसाला नूडल्स (₹14) चाहिए या मैगी आटा नूडल्स (₹25)?"*

**Presenter Voiceover**:
> "Notice that the customer simply said *'Maggi'*. Many voice assistants would guess blindly. But in a neighbourhood grocery store, delivering the wrong product destroys customer trust! 
> KiranaVaani's ambiguity gate flagged that both Masala and Atta Maggi exist in our 35-SKU catalog. It paused cart addition and asked for clarification."

**Visual**: Presenter clicks *"मैगी 2-मिनट मसाला (₹14)"*. The cart immediately updates to ₹88.00 total.

---

### 1:25 – 1:55 | Timbre v2.5 Voice Readback & Soundbox 2.0 Chime
**Visual**: Presenter clicks *"Listen to Spoken Readback"*.
**Audio Output**:
> *"Aapke order me 2 packet Maggi, 1 kg Sugar aur aadha litre Milk shamil hai. Kul bill 88 rupaye hua hai. Order confirm karein?"*

**Visual**: Presenter clicks *"Confirm Order"*. The **Kirana Soundbox 2.0** sounds its authentic merchant chime:
> 🔊 *"Gupta Kirana Soundbox: अट्ठासी रुपये का यूपीआई भुगतान प्राप्त हुआ!"*

**Visual**: Presenter clicks *"58mm Thermal POS Receipt"*. A realistic retro dot-matrix bill pops up with jagged tear edges, FSSAI/GSTIN details, and a scanable UPI QR code. Click *"Print"* to show printer preview!

---

### 1:55 – 2:20 | Bhasha-Sudhaar & Acoustic Confidence Heatmap
**Visual**: Switch screen to the **Acoustic Spectrogram**.
**Presenter Voiceover**:
> "Look at the **Phonetic Confidence Heatmap**: every token is scored acoustically in real-time. Notice how our **Bhasha-Sudhaar Engine** handles mid-sentence conversational repair: if a caller says *'5 kilo atta... arre nahi 5 nahi 2 kilo karna, aur Maggi mat bhejna'*, it rolls back the cancellation instantly without double-billing!
> And when telephony bandpass causes phonetic ambiguity, the shopkeeper can click any word on the heatmap to slice and replay the exact 0.8-second audio snippet."

---

### 2:20 – 2:40 | The Noise Lab & Keyterm Biasing Resilience
**Visual**: Switch screen to the **Noise Lab Results Plot** (`ablation_benchmark_plot.png`).
**Presenter Voiceover**:
> "Kirana stores are noisy places. In our **Telephony Noise Lab**, we benchmarked KiranaVaani across 80 synthetic orders through an 8 kHz ITU-T G.711 $\mu$-law telephony channel and ambient shop noise down to 0 dB SNR.
> When we injected **200 Kirana catalog keyterms** into Prisma v3.0's beam search, our business Item-F1 jumped from **59.4% to 84.6%** under extreme market noise. That is the power of domain-adapted Speech AI."

---

### 2:40 – 2:55 | Conclusion & Call to Action
**Visual**: Return to KiranaVaani Cockpit. Click "Confirm Order" — green confirmation banner flashes.
**Presenter Voiceover**:
> "KiranaVaani turns any neighbourhood grocery store into an AI-powered voice commerce hub. Built with pride for the **Great Indian AI Internship Challenge by Gnani.ai**. 
> Code and documentation are available open-source on GitHub. Dhanyavaad!"

---

## 3. Recommended Social Media Post Copy

```markdown
🚀 Excited to share **KiranaVaani (किरानावाणी)** — a noise-robust Hinglish voice assistant built for India's 12 million neighbourhood Kirana stores! 🛒🎙️

Submitted for the **Great Indian AI Internship Challenge by Gnani.ai** 🇮🇳

Key Highlights:
✨ **Gnani Prisma v3.0 Speech-to-Text**: Auto-LID (98.4%) code-mixed Hinglish recognition.
✨ **Colloquial Numeral Normalization**: Ingests Indian fractions like "सवा दो किलो", "ढाई किलो", "आधा लीटर".
✨ **Zero Silent Errors**: Guardrail ambiguity gate prevents billing errors when orders are ambiguous.
✨ **Gnani Timbre v2.5 Text-to-Speech**: Natural Indian voice confirmation readbacks.
✨ **Noise Lab Benchmark**: Evaluated across 8 kHz telephony codecs & 0 dB SNR market noise. 200 catalog keyterms lifted Item-F1 from 59.4% to 84.6%!

🌐 Live Cockpit (Render): https://kiranavaani.onrender.com
⚡ Live Cockpit (Vercel): https://kiranavaani.vercel.app
💻 Open-Source Code: https://github.com/vikassharma270907-alt/kiranavaani

A huge thank you to @Gnani.ai and its founders Ganesh Gopalan and Ananth Nagaraj for hosting the Great Indian AI Internship Challenge and championing frontier Indic voice technology!

#GnaniAI #GreatIndianAIInternshipChallenge #SpeechAI #VoiceAssistant #KiranaStores #NLP #DeepLearning #Python #FastAPI #React
```
