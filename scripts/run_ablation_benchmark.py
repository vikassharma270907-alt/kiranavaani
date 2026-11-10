"""
KiranaVaani Ablation Benchmark Runner
-------------------------------------
Evaluates Gnani Prisma v2.5 vs v3.0 (Keyterms ON vs OFF) across 5 acoustic SNR tiers:
Clean (+30 dB), Telephony (+20 dB), Fan (+10 dB), Traffic (+5 dB), and Market (0 dB).
Computes Word Error Rate (WER) and Item-Level F1 Score and saves plots to reports/.
"""

import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from backend.parser import HinglishOrderParser
from backend.noise_lab import NoiseLab

DATASET_PATH = Path(__file__).resolve().parent.parent / "reports" / "synthetic_80_test_set.json"
RESULTS_JSON = Path(__file__).resolve().parent.parent / "reports" / "ablation_benchmark_results.json"
PLOT_PNG = Path(__file__).resolve().parent.parent / "reports" / "ablation_benchmark_plot.png"

def run_ablation():
    if not DATASET_PATH.exists():
        from scripts.generate_synthetic_80 import generate_synthetic_dataset
        dataset = generate_synthetic_dataset(80)
    else:
        with open(DATASET_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            dataset = data.get("synthetic_samples", [])

    print(f"Loaded {len(dataset)} synthetic test samples for ablation benchmark.")

    parser = HinglishOrderParser()
    noise_lab = NoiseLab(parser=parser)

    res = noise_lab.run_acoustic_tier_benchmark(dataset)
    benchmark_tiers = res["benchmark"]

    # Print summary table
    print("\n" + "=" * 90)
    print("KIRANAVAANI NOISE-ROBUSTNESS & MODEL ABLATION BENCHMARK (GNANI PRISMA v3.0)")
    print("=" * 90)
    header = f"{'Acoustic Tier & Condition':<35} | {'v2.5 (No Key)':<16} | {'v3.0 (Key OFF)':<16} | {'v3.0 (Key ON)':<16}"
    print(header)
    print("-" * 90)

    for tier in benchmark_tiers:
        name = tier["tier_name"].split(":")[0] + f" ({tier['snr_db']}dB)"
        cfg = tier["configs"]
        v25 = f"{cfg['v25_no_key']['wer']}% / {cfg['v25_no_key']['item_f1']}%"
        v30_off = f"{cfg['v30_no_key']['wer']}% / {cfg['v30_no_key']['item_f1']}%"
        v30_on = f"{cfg['v30_key_on']['wer']}% / {cfg['v30_key_on']['item_f1']}%"
        print(f"{name:<35} | {v25:<16} | {v30_off:<16} | {v30_on:<16}")
    print("=" * 90)
    print("Values formatted as: WER (%) / Item-Level F1 (%)\n")

    # Save JSON results
    RESULTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print(f"Benchmark results saved to: {RESULTS_JSON}")

    # Generate Matplotlib visualization plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor("#0f172a")

    snrs = [tier["snr_db"] for tier in benchmark_tiers]
    snr_labels = [f"{tier['snr_db']} dB" for tier in benchmark_tiers]

    f1_v25 = [tier["configs"]["v25_no_key"]["item_f1"] for tier in benchmark_tiers]
    f1_v30_off = [tier["configs"]["v30_no_key"]["item_f1"] for tier in benchmark_tiers]
    f1_v30_on = [tier["configs"]["v30_key_on"]["item_f1"] for tier in benchmark_tiers]

    wer_v25 = [tier["configs"]["v25_no_key"]["wer"] for tier in benchmark_tiers]
    wer_v30_off = [tier["configs"]["v30_no_key"]["wer"] for tier in benchmark_tiers]
    wer_v30_on = [tier["configs"]["v30_key_on"]["wer"] for tier in benchmark_tiers]

    x = np.arange(len(snrs))
    width = 0.25

    for ax in [ax1, ax2]:
        ax.set_facecolor("#1e293b")
        ax.grid(color="#334155", linestyle="--", linewidth=0.7, alpha=0.7)
        ax.tick_params(colors="#cbd5e1", labelsize=10)
        for spine in ax.spines.values():
            spine.set_color("#475569")

    # Plot 1: Item-Level F1 (%)
    b1 = ax1.bar(x - width, f1_v25, width, label="Prisma v2.5 (No Keyterms)", color="#f43f5e")
    b2 = ax1.bar(x, f1_v30_off, width, label="Prisma v3.0 (Keyterms OFF)", color="#38bdf8")
    b3 = ax1.bar(x + width, f1_v30_on, width, label="Prisma v3.0 (200 Keyterms ON)", color="#10b981")

    ax1.set_title("Item-Level F1 (%) across Acoustic SNR Tiers (Higher is Better)", fontsize=12, fontweight="bold", color="#f8fafc", pad=12)
    ax1.set_xlabel("Acoustic Condition (SNR)", color="#94a3b8", fontsize=11)
    ax1.set_ylabel("Item-Level F1 (%)", color="#94a3b8", fontsize=11)
    ax1.set_xticks(x)
    ax1.set_xticklabels(snr_labels)
    ax1.set_ylim(40, 105)
    ax1.legend(facecolor="#0f172a", edgecolor="#334155", labelcolor="#f8fafc", fontsize=9)

    # Plot 2: Word Error Rate (%)
    ax2.plot(x, wer_v25, marker="o", linewidth=2.5, label="Prisma v2.5 (No Keyterms)", color="#f43f5e")
    ax2.plot(x, wer_v30_off, marker="s", linewidth=2.5, label="Prisma v3.0 (Keyterms OFF)", color="#38bdf8")
    ax2.plot(x, wer_v30_on, marker="^", linewidth=2.5, label="Prisma v3.0 (200 Keyterms ON)", color="#10b981")

    ax2.set_title("Word Error Rate (WER %) across SNR Tiers (Lower is Better)", fontsize=12, fontweight="bold", color="#f8fafc", pad=12)
    ax2.set_xlabel("Acoustic Condition (SNR)", color="#94a3b8", fontsize=11)
    ax2.set_ylabel("WER (%)", color="#94a3b8", fontsize=11)
    ax2.set_xticks(x)
    ax2.set_xticklabels(snr_labels)
    ax2.set_ylim(0, 40)
    ax2.legend(facecolor="#0f172a", edgecolor="#334155", labelcolor="#f8fafc", fontsize=9)

    plt.tight_layout()
    plt.savefig(PLOT_PNG, dpi=180, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    print(f"Publication-ready ablation plot saved to: {PLOT_PNG}")

if __name__ == "__main__":
    run_ablation()
