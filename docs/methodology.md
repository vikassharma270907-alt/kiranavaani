# KiranaVaani — Experimental Methodology & Acoustic Protocol

This document outlines the scientific methodology, acoustic degradation protocol, evaluation metrics, and ablation benchmark design of **KiranaVaani**.

---

## 1. Acoustic Channel Degradation Protocol

To scientifically evaluate voice assistant robustness in real Indian grocery environments, we simulate the combined effects of **telephony channel bandwidth compression** and **ambient acoustic noise**.

### 1.1. PSTN Telephony Codec (ITU-T G.711 $\mu$-Law)
Telephony audio in India travels over circuit-switched PSTN or cellular voice channels with strict acoustic limits:
1. **Sampling Rate**: Downsampled to $8\text{ kHz}$ ($8,000\text{ samples/sec}$).
2. **Frequency Filtering**: A 4th-order Butterworth bandpass filter ($300\text{ Hz}$ to $3400\text{ Hz}$) removes low-frequency room modes and high-frequency sibilants.
3. **Logarithmic Quantization**: Signal dynamic range is compressed using standard $\mu$-law with parameter $\mu = 255$:
   $$F(x) = \text{sgn}(x) \frac{\ln(1 + 255 |x|)}{\ln(256)}, \quad -1 \le x \le 1$$
4. **8-bit Word Conversion**: Signals are rounded to 256 discrete levels ($[-128, 127]$), introducing realistic quantization noise, followed by inverse expansion:
   $$F^{-1}(y) = \text{sgn}(y) \frac{1}{255} \left( 256^{|y|} - 1 \right)$$

### 1.2. Acoustic Noise Injections
We model three real-world noise sources common in Indian retail:
- **Shop Ceiling Fan (50 Hz Hum)**: Fundamental $50\text{ Hz}$ powerline hum with $100\text{ Hz}$ and $150\text{ Hz}$ motor blade harmonics and turbulent air noise.
- **Street Traffic & Pressure Horns**: Low-pass filtered road friction ($< 400\text{ Hz}$) coupled with intermittent dual-tone horns ($440\text{ Hz} + 580\text{ Hz}$).
- **Market Babble**: Speech-shaped multi-talker commotion bandpassed between $200\text{ Hz}$ and $2800\text{ Hz}$.

---

## 2. Signal-to-Noise Ratio (SNR) Calibrations

Signals are mixed using Root-Mean-Square (RMS) power matching across five standard tiers:

$$\text{SNR}_{\text{dB}} = 10 \log_{10} \left( \frac{P_{\text{speech}}}{P_{\text{noise}}} \right)$$

The noise scale factor $\alpha$ is computed as:

$$\alpha = \sqrt{ \frac{P_{\text{speech}}}{P_{\text{noise}} \cdot 10^{\text{SNR}_{\text{target}} / 10}} }$$

$$\text{signal}_{\text{degraded}}(t) = \text{clip} \left( \text{signal}_{\text{telephony}}(t) + \alpha \cdot \text{noise}(t), -1.0, 1.0 \right)$$

| Degradation Tier | Acoustic Profile | Channel Bandwidth | Target SNR |
| :--- | :--- | :--- | :--- |
| **Tier 1** | Clean Studio Reference | 16 kHz Wideband | +30 dB |
| **Tier 2** | PSTN Line Noise | 8 kHz Bandpass + G.711 $\mu$-law | +20 dB |
| **Tier 3** | Ceiling Fan Hum | 8 kHz Bandpass + G.711 $\mu$-law | +10 dB |
| **Tier 4** | Street Traffic & Horns | 8 kHz Bandpass + G.711 $\mu$-law | +5 dB |
| **Tier 5** | Heavy Market Babble | 8 kHz Bandpass + G.711 $\mu$-law | 0 dB |

---

## 3. Evaluation Metrics

### 3.1. Word Error Rate (WER)
Evaluates automatic speech recognition output fidelity against the ground truth reference:

$$\text{WER} = \frac{\text{Substitutions} + \text{Deletions} + \text{Insertions}}{N_{\text{reference words}}} \times 100\%$$

### 3.2. Item-Level Precision, Recall, and F1
Evaluating grocery voice assistants purely on WER is insufficient: if a model transcribes *"ek"* as *"do"*, WER changes by only 1 word, but the customer receives double the order.

Therefore, we enforce **strict business-critical item-level metrics**:
- **True Positive (TP)**: Both the canonical `sku_id` AND the normalized numerical quantity match the ground truth.
- **False Positive (FP)**: An item or incorrect quantity added to the cart that was not ordered.
- **False Negative (FN)**: An item requested by the caller that was missed or rejected.

$$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}} \times 100\%, \quad \text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}} \times 100\%$$

$$F_1 = \frac{2 \cdot \text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$

---

## 4. Model Ablation Matrix

We evaluate three model configurations across all 5 SNR tiers:
1. **Prisma v2.5 (No Keyterms)**: Legacy speech recognition model without catalog biasing.
2. **Prisma v3.0 (Keyterms OFF)**: Next-generation multilingual STT with Auto-LID, but without vocabulary boosting.
3. **Prisma v3.0 (200 Keyterms ON)**: Prisma v3.0 with dynamic beam search keyterm biasing utilizing the 200 Kirana catalog aliases.

---

## 5. Synthetic Dataset & Privacy Guarantees

- **Sample Size**: 80 synthetic test orders containing 192 individual item requests.
- **Zero-PII Compliance**: All caller names, transcripts, and items are 100% synthetically generated.
- No real customer phone numbers, Aadhaar IDs, or private voice recordings are collected, processed, or stored.
