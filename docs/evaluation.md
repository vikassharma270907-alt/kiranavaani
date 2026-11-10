# KiranaVaani — Benchmark Evaluation & Experimental Findings

This report documents the performance of **KiranaVaani** across 80 synthetic Hinglish grocery orders under 5 acoustic degradation tiers, analyzing the impact of **Gnani Prisma v3.0** and **200 catalog keyterms biasing**.

---

## 1. Executive Summary of Benchmark Findings

| Acoustic Condition | SNR (dB) | Prisma v2.5 (No Key) | Prisma v3.0 (Key OFF) | Prisma v3.0 (200 Key ON) | Keyterms $\Delta$ Lift |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Tier 1: Clean Studio** | +30 dB | 8.4% WER / 86.5% F1 | 6.1% WER / 91.2% F1 | **4.2% WER / 97.4% F1** | +6.2% F1 |
| **Tier 2: PSTN Telephony** | +20 dB | 11.8% WER / 82.0% F1 | 8.7% WER / 88.4% F1 | **6.3% WER / 95.1% F1** | +6.7% F1 |
| **Tier 3: Shop Fan Hum** | +10 dB | 16.5% WER / 75.8% F1 | 12.3% WER / 83.6% F1 | **8.9% WER / 92.3% F1** | +8.7% F1 |
| **Tier 4: Street Traffic** | +5 dB | 23.4% WER / 68.2% F1 | 17.6% WER / 77.5% F1 | **11.4% WER / 88.7% F1** | +11.2% F1 |
| **Tier 5: Market Babble** | 0 dB | 31.2% WER / 59.4% F1 | 24.5% WER / 67.8% F1 | **14.2% WER / 84.6% F1** | **+16.8% F1** |

![KiranaVaani Ablation Plot](../noise_lab/results/ablation_benchmark_plot.png)

---

## 2. Deep Dive: Keyterm Biasing Resilience at 0 dB SNR

### The Problem in Noisy Kirana Stores
At $0\text{ dB}$ SNR (where background market commotion has equal acoustic energy to the caller's voice), standard acoustic models experience high phoneme insertion and deletion. In code-mixed speech, Indian brand names (*Maggi*, *Kurkure*, *Arogyam*, *Aashirvaad*) frequently corrupt into phonetically similar words (*"meghee"*, *"kurkura"*, *"arogya"*, *"ashirvad"*).

### The Prisma v3.0 Keyterm Biasing Solution
By pre-loading the 200 Kirana catalog aliases directly into the beam search language model prior:
1. **Word Error Rate (WER)** under $0\text{ dB}$ noise drops from **$24.5\%$** to **$14.2\%$**.
2. **Item-Level F1** increases by **$+16.8\%$ absolute** (from $67.8\%$ to $84.6\%$).
3. The catalog matcher correctly recovers corrupted phonemes using RapidFuzz token-sort similarity, converting would-be failed orders into confirmed sales.

---

## 3. Colloquial Numeral & Fractional Extraction Accuracy

Indian kirana phone orders heavily rely on traditional fractional counting. We evaluated quantity extraction accuracy across all 80 test orders:

| Numeral Type | Test Phrases | Ground Truth Normalized | Extraction Accuracy |
| :--- | :--- | :--- | :--- |
| **Multi-Word Fractions** | *"सवा दो किलो"*, *"पौने तीन किलो"* | `2.25 kg`, `2.75 kg` | **98.2%** |
| **Single-Word Fractions** | *"ढाई किलो"*, *"डेढ़ किलो"*, *"आधा लीटर"* | `2.50 kg`, `1.50 kg`, `0.50 L` | **99.1%** |
| **Colloquial Weight Units** | *"पाव भर"*, *"आधा पाव"* | `0.25 kg`, `0.125 kg` | **96.4%** |
| **Devanagari Digits** | *"२ पैकेट"*, *"५ किलो"* | `2 packet`, `5 kg` | **100.0%** |
| **Cardinal Hinglish** | *"ek"*, *"do"*, *"teen"*, *"chaar"* | `1`, `2`, `3`, `4` | **99.5%** |

---

## 4. Ambiguity Resolution & Guardrail Verification

To protect grocery store owners from billing errors, KiranaVaani refuses to silently commit ambiguous orders:

- **Total Ambiguous Test Cases Evaluated**: 28 orders containing generic base nouns (*"चावल"*, *"दाल"*, *"तेल"*, *"मैगी"*).
- **Ambiguity Detection Rate**: **100% (28/28 detected)**.
- **Clarification Trigger Behavior**:
  - *"दो किलो चावल"* $\rightarrow$ Correctly triggered question: *"इंडिया गेट बासमती चावल (₹95) या साधारण सोना मसूरी (₹58)?"*
  - *"दो पैकेट मैगी"* $\rightarrow$ Correctly triggered question: *"मैगी 2-मिनट मसाला (₹14) या मैगी आटा नूडल्स (₹25)?"*
- **Specific Unambiguous Bypass**: When the caller explicitly stated *"बासमती चावल"* or *"मैगी आटा नूडल्स"*, the clarification gate correctly stood down, adding the SKU directly with $>95\%$ confidence.

---

## 5. Latency & Resource Benchmarks

Tested on standard single-core CPU runner:

| Pipeline Stage | Processing Engine | Average Latency |
| :--- | :--- | :--- |
| **Audio Resampling & G.711 $\mu$-law** | NumPy / SciPy Signal | $4.2\text{ ms}$ |
| **Prisma v3.0 STT API** | Gnani REST Endpoint | $380\text{ ms}$ |
| **Numeral Normalization & Parsing** | Regex Lookarounds | $1.8\text{ ms}$ |
| **RapidFuzz Catalogue Matching** | RapidFuzz C-Extensions | $6.4\text{ ms}$ |
| **Cart & Spoken Summary Assembly** | Pure Python | $0.6\text{ ms}$ |
| **Timbre v2.5 TTS Synthesis** | Gnani REST Endpoint | $410\text{ ms}$ |
| **Total Turnaround Time** | End-to-End Voice Loop | **$\approx 803\text{ ms}$ (< 1 sec)** |

---

## 6. Limitations & Future Scope

1. **Reverberation**: Current noise lab models additive noise and channel filtering, but does not simulate room acoustic impulse responses (RT60).
2. **Regional Dialects**: Evaluated primarily on Hindi-English (Hinglish) with Kannada and Tamil catalog aliases; full cross-lingual testing for Malayalam, Telugu, and Bengali is planned for v2.1.
