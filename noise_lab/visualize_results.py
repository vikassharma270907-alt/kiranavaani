"""
Visualization Module for Noise Lab Benchmark Results.
Generates publication-quality charts using Matplotlib:
1. Word Error Rate (WER %) vs Acoustic SNR (dB)
2. Business-Critical Item F1 (%) vs Acoustic SNR (dB) with Keyterms Biasing
3. Clean vs 0 dB Market Babble Comparison
Saves outputs to noise_lab/results/ and reports/.
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def generate_visualizations(
    results_path: Optional[Path] = None,
    output_png: Optional[Path] = None
) -> Path:
    base_dir = Path(__file__).resolve().parent
    res_path = results_path or (base_dir / "results" / "evaluation_results.json")
    if not res_path.exists():
        # Try alternate path
        alt = base_dir.parent / "reports" / "ablation_benchmark_results.json"
        if alt.exists():
            res_path = alt
        else:
            raise FileNotFoundError(f"Evaluation results not found at {res_path}")

    with open(res_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    tiers = data.get("results", data.get("benchmark", []))

    snr_levels = []
    tier_labels = []
    v25_wer, v25_f1 = [], []
    v30_off_wer, v30_off_f1 = [], []
    v30_on_wer, v30_on_f1 = [], []

    for t in tiers:
        snr = t["snr_db"]
        snr_levels.append(snr)
        tier_labels.append(f"{t['tier_name'].split(':')[0]} ({snr}dB)")
        cfg = t["configs"]

        # Support both naming conventions
        k25 = cfg.get("v25_no_key", {})
        k30_off = cfg.get("v30_key_off", cfg.get("v30_no_key", {}))
        k30_on = cfg.get("v30_key_on", {})

        v25_wer.append(k25.get("wer", 0.0))
        v25_f1.append(k25.get("item_f1", 0.0))

        v30_off_wer.append(k30_off.get("wer", 0.0))
        v30_off_f1.append(k30_off.get("item_f1", 0.0))

        v30_on_wer.append(k30_on.get("wer", 0.0))
        v30_on_f1.append(k30_on.get("item_f1", 0.0))

    # Create figure with 2 subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)
    plt.subplots_adjust(wspace=0.25)

    # Style colors
    c_v25 = "#ef4444"      # Red
    c_v30_off = "#f59e0b"  # Amber
    c_v30_on = "#10b981"   # Emerald green

    # 1. Left Plot: Word Error Rate (WER) vs SNR
    ax1.plot(snr_levels, v25_wer, marker="o", linewidth=2.2, color=c_v25, label="Prisma v2.5 (No Keyterms)")
    ax1.plot(snr_levels, v30_off_wer, marker="s", linewidth=2.2, color=c_v30_off, label="Prisma v3.0 (Keyterms OFF)")
    ax1.plot(snr_levels, v30_on_wer, marker="^", linewidth=2.8, color=c_v30_on, label="Prisma v3.0 (200 Keyterms ON)")

    ax1.set_title("Word Error Rate (WER ↓) vs Acoustic Noise", fontsize=12, fontweight="bold", pad=12)
    ax1.set_xlabel("Signal-to-Noise Ratio (SNR in dB) [Clean → Noisy]", fontsize=10, fontweight="semibold")
    ax1.set_ylabel("Word Error Rate (%)", fontsize=10, fontweight="semibold")
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="upper right", framealpha=0.9)
    ax1.invert_xaxis()  # 30 dB (clean) on left, 0 dB (noisy) on right

    # 2. Right Plot: Item-Level F1 Score vs SNR
    ax2.plot(snr_levels, v25_f1, marker="o", linewidth=2.2, color=c_v25, label="Prisma v2.5 (No Keyterms)")
    ax2.plot(snr_levels, v30_off_f1, marker="s", linewidth=2.2, color=c_v30_off, label="Prisma v3.0 (Keyterms OFF)")
    ax2.plot(snr_levels, v30_on_f1, marker="^", linewidth=2.8, color=c_v30_on, label="Prisma v3.0 (200 Keyterms ON)")

    # Highlight key resilience delta at 0 dB
    delta_f1 = v30_on_f1[-1] - v30_off_f1[-1]
    ax2.annotate(
        f"+{delta_f1:.1f}% F1 Boost\nwith Keyterms",
        xy=(snr_levels[-1], v30_on_f1[-1]),
        xytext=(snr_levels[-1] + 5, v30_on_f1[-1] - 8),
        arrowprops=dict(facecolor="#059669", shrink=0.08, width=1.5, headwidth=6),
        fontsize=9,
        fontweight="bold",
        color="#065f46",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#ecfdf5", edgecolor="#a7f3d0")
    )

    ax2.set_title("Business Item F1 Score (F1 ↑) vs Acoustic Noise", fontsize=12, fontweight="bold", pad=12)
    ax2.set_xlabel("Signal-to-Noise Ratio (SNR in dB) [Clean → Noisy]", fontsize=10, fontweight="semibold")
    ax2.set_ylabel("Item-Level F1 Score (%)", fontsize=10, fontweight="semibold")
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="lower left", framealpha=0.9)
    ax2.invert_xaxis()

    fig.suptitle(
        "KiranaVaani: Telephony & Environmental Noise-Robustness Study\n(Gnani AI Prisma v3.0 Beam Search Keyterms Biasing Impact)",
        fontsize=13,
        fontweight="bold",
        y=1.02
    )

    out_file = output_png or (base_dir / "results" / "ablation_benchmark_plot.png")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_file, bbox_inches="tight")
    plt.close()

    print(f"Visualization successfully saved to: {out_file}")
    return out_file


if __name__ == "__main__":
    generate_visualizations()
