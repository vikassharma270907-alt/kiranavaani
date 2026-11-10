"""
End-to-End Order Evaluation Module.
Evaluates the complete pipeline (ASR -> Parsing -> Catalogue Matching) across SNR tiers
and compares Prisma v2.5 vs v3.0 with Keyterms ON vs OFF.
Computes Item Precision, Recall, F1-Score, and Quantity Exact-Match Accuracy.
Outputs results to JSON and CSV.
"""
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from noise_lab.metrics import calculate_wer, calculate_item_metrics, calculate_quantity_accuracy
from noise_lab.evaluate_asr import simulate_noisy_transcript, SNR_TIERS
from backend.app.services.order_parser import order_parser
from backend.app.services.catalogue_matcher import catalogue_matcher

logger = logging.getLogger(__name__)


def run_order_evaluation(
    samples: List[Dict[str, Any]],
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Runs end-to-end evaluation on grocery order samples across all acoustic degradation tiers.
    """
    tier_results = []
    csv_rows = []

    for tier in SNR_TIERS:
        snr = tier["snr_db"]
        tier_data = {
            "tier_name": tier["name"],
            "snr_db": snr,
            "noise_type": tier["noise_type"],
            "configs": {}
        }

        configurations = [
            ("v25_no_key", "prisma-v2.5", False),
            ("v30_key_off", "prisma-v3.0", False),
            ("v30_key_on", "prisma-v3.0", True),
        ]

        for cfg_key, model_ver, key_flag in configurations:
            total_wer = 0.0
            all_gt_items = []
            all_pred_items = []
            ambiguity_count = 0

            for sample in samples:
                clean_ref = sample.get("clean_text", sample.get("transcript", ""))
                gt_items = sample.get("ground_truth_items", [])

                # 1. Simulate noisy transcript for this acoustic condition
                hyp_transcript = simulate_noisy_transcript(clean_ref, snr, key_flag, model_ver)
                wer = calculate_wer(clean_ref, hyp_transcript)
                total_wer += wer

                # 2. Parse utterance into items, quantities, and units
                parsed = order_parser.parse_utterance(hyp_transcript, keyterms_enabled=key_flag)

                # 3. Match against catalogue
                matched = catalogue_matcher.match_items(parsed.items, keyterms_enabled=key_flag)

                # Collect predicted items (confirmed matches)
                pred_items = []
                for m in matched.matched_items:
                    if m.status == "MATCHED" and m.matched_sku:
                        pred_items.append({
                            "sku_id": m.matched_sku.sku_id,
                            "name": m.matched_sku.name_en,
                            "qty": m.original_item.quantity,
                            "unit": m.original_item.unit
                        })
                    elif m.status == "CLARIFICATION_REQUIRED":
                        ambiguity_count += 1

                all_gt_items.extend(gt_items)
                all_pred_items.extend(pred_items)

            # Compute aggregate metrics for this tier and configuration
            avg_wer = round(total_wer / max(len(samples), 1), 2)
            item_metrics = calculate_item_metrics(all_gt_items, all_pred_items)
            qty_acc = calculate_quantity_accuracy(all_gt_items, all_pred_items)

            cfg_result = {
                "wer": avg_wer,
                "precision": item_metrics["precision"],
                "recall": item_metrics["recall"],
                "item_f1": item_metrics["item_f1"],
                "quantity_accuracy": qty_acc,
                "ambiguities_flagged": ambiguity_count,
                "total_orders_evaluated": len(samples)
            }
            tier_data["configs"][cfg_key] = cfg_result

            csv_rows.append({
                "tier_name": tier["name"],
                "snr_db": snr,
                "config": cfg_key,
                "model": model_ver,
                "keyterms_enabled": key_flag,
                "wer": avg_wer,
                "precision": item_metrics["precision"],
                "recall": item_metrics["recall"],
                "item_f1": item_metrics["item_f1"],
                "quantity_accuracy": qty_acc,
                "ambiguities_flagged": ambiguity_count
            })

        tier_results.append(tier_data)

    final_report = {
        "benchmark_title": "KiranaVaani Noise-Robustness & Keyterms Ablation Benchmark",
        "dataset_size": len(samples),
        "results": tier_results
    }

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        json_out = output_dir / "evaluation_results.json"
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)

        csv_out = output_dir / "evaluation_results.csv"
        if csv_rows:
            with open(csv_out, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
                writer.writeheader()
                writer.writerows(csv_rows)

    return final_report


if __name__ == "__main__":
    data_path = Path(__file__).resolve().parent.parent / "data" / "sample_orders.json"
    if data_path.exists():
        with open(data_path, "r", encoding="utf-8") as f:
            d = json.load(f)
            samples_list = d.get("synthetic_samples", d.get("samples", []))
        out_folder = Path(__file__).resolve().parent / "results"
        res = run_order_evaluation(samples_list, output_dir=out_folder)
        print("\n==========================================================================================")
        print("KIRANAVAANI NOISE-ROBUSTNESS BENCHMARK RESULTS")
        print("==========================================================================================")
        header = f"{'Tier / Condition':<28} | {'v2.5 (No Key) WER/F1':<22} | {'v3.0 (Key OFF) WER/F1':<22} | {'v3.0 (Key ON) WER/F1':<22}"
        print(header)
        print("-" * 100)
        for t in res["results"]:
            c = t["configs"]
            v25 = f"{c['v25_no_key']['wer']}% / {c['v25_no_key']['item_f1']}%"
            v30_off = f"{c['v30_key_off']['wer']}% / {c['v30_key_off']['item_f1']}%"
            v30_on = f"{c['v30_key_on']['wer']}% / {c['v30_key_on']['item_f1']}%"
            print(f"{t['tier_name']:<28} | {v25:<22} | {v30_off:<22} | {v30_on:<22}")
        print("==========================================================================================\n")
