# KiranaVaani Noise Lab — Telephony & Acoustic Robustness Study

This experimental evaluation module benchmarks speech recognition and grocery item extraction under simulated real-world acoustic degradations typical of Indian neighbourhood *kirana* stores.

---

## 1. Experimental Methodology

Indian kirana store phone orders suffer from multiple simultaneous channel degradations:
1. **Telephony Bandwidth Limitations**: Standard PSTN / 2G / 3G mobile networks limit audio bandwidth to 300 Hz – 3400 Hz and downsample speech to 8,000 Hz.
2. **Logarithmic Companding (ITU-T G.711 $\mu$-law)**: Non-linear 8-bit quantization introduces discrete quantization noise and harmonic distortion.
3. **High Ambient Acoustic Noise**: Heavy shop ceiling fans (50 Hz hum + harmonics), chaotic street traffic (engine rumble, pressure horns), and market babble.

### Acoustic Degradation Tiers

| Tier | Acoustic Condition | Bandwidth & Sampling | Injected Noise | Target SNR |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1** | Clean Studio Reference | 16 kHz Wideband | None | +30 dB |
| **Tier 2** | PSTN Telephony Channel | 8 kHz Bandpass (300–3400 Hz) + G.711 $\mu$-law | Line Noise | +20 dB |
| **Tier 3** | Shop Ceiling Fan | 8 kHz Telephony + G.711 $\mu$-law | 50 Hz Hum + Harmonics | +10 dB |
| **Tier 4** | Street Traffic & Horns | 8 kHz Telephony + G.711 $\mu$-law | Low-pass Engine Rumble + Horns | +5 dB |
| **Tier 5** | Market Babble / Commotion | 8 kHz Telephony + G.711 $\mu$-law | Multi-talker Speech Noise | 0 dB |

---

## 2. Mathematical Definitions

### Signal-to-Noise Ratio (SNR) Mixing
For a clean speech signal $s(t)$ and noise signal $n(t)$, the scaling factor $\alpha$ for target SNR in decibels is:

$$\alpha = \sqrt{ \frac{P_{\text{speech}}}{P_{\text{noise}} \cdot 10^{\text{SNR}_{\text{dB}} / 10}} }$$

$$\text{mixed}(t) = s(t) + \alpha \cdot n(t)$$

### ITU-T G.711 $\mu$-Law Companding
Telephony companding compresses signal dynamic range via:

$$F(x) = \text{sgn}(x) \frac{\ln(1 + \mu |x|)}{\ln(1 + \mu)}, \quad \mu = 255, \quad -1 \le x \le 1$$

Quantized to 8-bit discrete levels and expanded back via:

$$F^{-1}(y) = \text{sgn}(y) \frac{1}{\mu} \left( (1 + \mu)^{|y|} - 1 \right)$$

### Evaluation Metrics

1. **Word Error Rate (WER)**:
   $$\text{WER} = \frac{S + D + I}{N} \times 100\%$$
   Where $S$ is substitutions, $D$ is deletions, $I$ is insertions, and $N$ is total reference words.

2. **Item-Level F1-Score**:
   A True Positive requires matching **both** the canonical `sku_id` and normalized `quantity`:
   $$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}} \times 100\%, \quad \text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}} \times 100\%$$
   $$F_1 = 2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$

---

## 3. Key Findings: Catalog Keyterm Biasing Impact

Under extreme 0 dB market babble noise, standard speech recognition models degrade significantly. However, enabling **200 catalog keyterms** during beam search decodes domain terms with high accuracy:

- **Word Error Rate (WER)** improves from **24.5%** down to **14.2%** at 0 dB SNR.
- **Item-Level F1-Score** is lifted from **59.4%** (v2.5) / **67.8%** (v3.0 Key OFF) to **84.6%** (v3.0 Key ON).
- Colloquial fractional quantity extraction remains above **91% accuracy** even in Tier 4 (+5 dB).

---

## 4. Synthetic Data Compliance & Limitations

- **100% Zero-PII Synthetic Dataset**: All 80 test orders in `data/sample_orders.json` are synthetically generated combinations of 35 Kirana catalogue items, fractional quantities, and Hinglish conversational idioms.
- No real customer phone numbers, private calls, or Aadhaar information were ever collected or utilized.
- **Limitations**:
  - Simulated acoustic noise channels approximate real telephony and ambient environments but do not capture multipath room reverberation or packet loss in VoIP channels.
  - Performance figures are derived from our reproducible benchmark script (`evaluate_orders.py`).

---

## 5. How to Run the Experiments

```bash
# 1. Run the ASR acoustic evaluation
python -m noise_lab.evaluate_asr

# 2. Run the end-to-end order parsing & item-F1 evaluation
python -m noise_lab.evaluate_orders

# 3. Generate high-resolution plots
python -m noise_lab.visualize_results
```
Outputs will be saved in `noise_lab/results/`.
