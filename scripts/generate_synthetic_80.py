"""
KiranaVaani Synthetic Test Dataset Generator
--------------------------------------------
Generates 80 synthetic kirana voice order utterances with exact ground truth
item/quantity annotations across 5 acoustic SNR tiers.

COMPLIANCE NOTICE:
100% Synthetic Data. Zero PII, zero real phone numbers, zero Aadhaar/PAN.
Built strictly for the Gnani.ai Great Indian AI Internship Challenge.
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Any

DATASET_OUT = Path(__file__).resolve().parent.parent / "reports" / "synthetic_80_test_set.json"

TEMPLATES = [
    # Template A: 2 items with integer quantities
    {
        "template": "भैया {qty1} {unit1} {name1} और {qty2} {unit2} {name2} लिख लो, बस इतना ही",
        "fractions": False
    },
    # Template B: 3 items with colloquial fractions
    {
        "template": "नमस्ते गुप्ता जी, {qty_word1} {name1}, {qty_word2} {name2} और {qty3} {unit3} {name3} देना, हो गया",
        "fractions": True
    },
    # Template C: Code-mixed brand order
    {
        "template": "Please send {qty1} {unit1} {name1}, {qty2} {unit2} {name2} and {qty3} {unit3} {name3}, that's all",
        "fractions": False
    },
    # Template D: Single item quick buy
    {
        "template": "भैया केवल {qty_word1} {name1} पैक कर दो, बिल बना दो",
        "fractions": True
    },
    # Template E: Multi-item grocery restocking
    {
        "template": "{qty1} {unit1} {name1}, {qty_word2} {name2}, {qty3} {unit3} {name3} और {qty4} {unit4} {name4}, बस इतना ही है",
        "fractions": True
    }
]

FRACTION_MAP = [
    ("आधा किलो", "aadha kilo", 0.5, "kg"),
    ("पाव भर", "paav bhar", 0.25, "kg"),
    ("सवा किलो", "sawa kilo", 1.25, "kg"),
    ("सवा दो किलो", "sawa do kilo", 2.25, "kg"),
    ("डेढ़ किलो", "dedh kilo", 1.5, "kg"),
    ("ढाई किलो", "dhai kilo", 2.5, "kg"),
    ("साढ़े तीन किलो", "saadhe teen kilo", 3.5, "kg")
]

def generate_synthetic_dataset(count: int = 80) -> List[Dict[str, Any]]:
    # Load catalog
    catalog_path = Path(__file__).resolve().parent.parent / "catalog" / "kirana_catalog_35_skus.json"
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)
    skus = catalog["skus"]

    # Filter out pure ambiguous root families for clean ground truth
    clean_skus = [s for s in skus if s["ambiguous_family"] is None or "masala" in s["name_en"].lower() or "basmati" in s["name_en"].lower() or "toor" in s["name_en"].lower() or "sunlight" in s["name_en"].lower() or "chakki" in s["name_en"].lower()]

    samples = []
    random.seed(42)

    tier_cycle = [30, 20, 10, 5, 0]

    for i in range(1, count + 1):
        target_snr = tier_cycle[(i - 1) % len(tier_cycle)]
        tmpl_info = TEMPLATES[(i - 1) % len(TEMPLATES)]
        tmpl = tmpl_info["template"]

        chosen = random.sample(clean_skus, 4)
        gt_items = []

        # Populate slots
        q1 = random.choice([1, 2, 3, 5])
        q2 = random.choice([1, 2, 4])
        q3 = random.choice([1, 2, 3])
        q4 = random.choice([1, 2])

        frac1 = random.choice(FRACTION_MAP)
        frac2 = random.choice(FRACTION_MAP)

        # Build ground truth based on template
        if tmpl_info == TEMPLATES[0]:
            text = tmpl.format(
                qty1=q1, unit1=chosen[0]["unit"], name1=chosen[0]["name_hi"],
                qty2=q2, unit2=chosen[1]["unit"], name2=chosen[1]["name_hi"]
            )
            gt_items = [
                {"sku_id": chosen[0]["sku_id"], "name": chosen[0]["name_en"], "qty": float(q1), "unit": chosen[0]["unit"]},
                {"sku_id": chosen[1]["sku_id"], "name": chosen[1]["name_en"], "qty": float(q2), "unit": chosen[1]["unit"]}
            ]
        elif tmpl_info == TEMPLATES[1]:
            text = tmpl.format(
                qty_word1=frac1[0], name1=chosen[0]["name_hi"],
                qty_word2=frac2[0], name2=chosen[1]["name_hi"],
                qty3=q3, unit3=chosen[2]["unit"], name3=chosen[2]["name_hi"]
            )
            gt_items = [
                {"sku_id": chosen[0]["sku_id"], "name": chosen[0]["name_en"], "qty": frac1[2], "unit": frac1[3]},
                {"sku_id": chosen[1]["sku_id"], "name": chosen[1]["name_en"], "qty": frac2[2], "unit": frac2[3]},
                {"sku_id": chosen[2]["sku_id"], "name": chosen[2]["name_en"], "qty": float(q3), "unit": chosen[2]["unit"]}
            ]
        elif tmpl_info == TEMPLATES[2]:
            text = tmpl.format(
                qty1=q1, unit1=chosen[0]["unit"], name1=chosen[0]["name_en"],
                qty2=q2, unit2=chosen[1]["unit"], name2=chosen[1]["name_en"],
                qty3=q3, unit3=chosen[2]["unit"], name3=chosen[2]["name_en"]
            )
            gt_items = [
                {"sku_id": chosen[0]["sku_id"], "name": chosen[0]["name_en"], "qty": float(q1), "unit": chosen[0]["unit"]},
                {"sku_id": chosen[1]["sku_id"], "name": chosen[1]["name_en"], "qty": float(q2), "unit": chosen[1]["unit"]},
                {"sku_id": chosen[2]["sku_id"], "name": chosen[2]["name_en"], "qty": float(q3), "unit": chosen[2]["unit"]}
            ]
        elif tmpl_info == TEMPLATES[3]:
            text = tmpl.format(
                qty_word1=frac1[0], name1=chosen[0]["name_hi"]
            )
            gt_items = [
                {"sku_id": chosen[0]["sku_id"], "name": chosen[0]["name_en"], "qty": frac1[2], "unit": frac1[3]}
            ]
        else:
            text = tmpl.format(
                qty1=q1, unit1=chosen[0]["unit"], name1=chosen[0]["name_hi"],
                qty_word2=frac2[0], name2=chosen[1]["name_hi"],
                qty3=q3, unit3=chosen[2]["unit"], name3=chosen[2]["name_hi"],
                qty4=q4, unit4=chosen[3]["unit"], name4=chosen[3]["name_hi"]
            )
            gt_items = [
                {"sku_id": chosen[0]["sku_id"], "name": chosen[0]["name_en"], "qty": float(q1), "unit": chosen[0]["unit"]},
                {"sku_id": chosen[1]["sku_id"], "name": chosen[1]["name_en"], "qty": frac2[2], "unit": frac2[3]},
                {"sku_id": chosen[2]["sku_id"], "name": chosen[2]["name_en"], "qty": float(q3), "unit": chosen[2]["unit"]},
                {"sku_id": chosen[3]["sku_id"], "name": chosen[3]["name_en"], "qty": float(q4), "unit": chosen[3]["unit"]}
            ]

        sample_record = {
            "sample_id": f"SYN-{i:03d}",
            "target_snr_db": target_snr,
            "acoustic_tier": f"{target_snr} dB {'Clean' if target_snr == 30 else 'Noisy Telephony'}",
            "caller_id": f"SyntheticCaller_{i % 12 + 1}",
            "transcript": text,
            "ground_truth_items": gt_items
        }
        samples.append(sample_record)

    return samples

if __name__ == "__main__":
    DATASET_OUT.parent.mkdir(parents=True, exist_ok=True)
    dataset = generate_synthetic_dataset(80)
    with open(DATASET_OUT, "w", encoding="utf-8") as f:
        json.dump({"synthetic_samples": dataset, "count": len(dataset)}, f, ensure_ascii=False, indent=2)
    print(f"Successfully generated {len(dataset)} synthetic test utterances -> {DATASET_OUT}")
