"""
Noise Lab Metrics Module.
Calculates Word Error Rate (WER), Item-level Precision, Recall, F1-Score,
and Quantity Accuracy across experimental acoustic conditions.
"""
from typing import List, Dict, Any, Tuple
import re

try:
    import jiwer
    HAS_JIWER = True
except ImportError:
    HAS_JIWER = False


def levenshtein_distance(seq1: List[str], seq2: List[str]) -> int:
    """Computes token-level Levenshtein edit distance between two token lists."""
    size_x = len(seq1) + 1
    size_y = len(seq2) + 1
    matrix = [[0] * size_y for _ in range(size_x)]

    for x in range(size_x):
        matrix[x][0] = x
    for y in range(size_y):
        matrix[0][y] = y

    for x in range(1, size_x):
        for y in range(1, size_y):
            if seq1[x - 1] == seq2[y - 1]:
                matrix[x][y] = matrix[x - 1][y - 1]
            else:
                matrix[x][y] = min(
                    matrix[x - 1][y] + 1,      # Deletion
                    matrix[x][y - 1] + 1,      # Insertion
                    matrix[x - 1][y - 1] + 1   # Substitution
                )
    return matrix[len(seq1)][len(seq2)]


def calculate_wer(reference: str, hypothesis: str) -> float:
    """
    Calculates Word Error Rate (WER) as percentage (0% to 100%+):
    WER = (S + D + I) / N
    """
    ref_clean = re.sub(r"[^\w\s\u0900-\u097F]", "", reference.lower()).strip()
    hyp_clean = re.sub(r"[^\w\s\u0900-\u097F]", "", hypothesis.lower()).strip()

    if not ref_clean and not hyp_clean:
        return 0.0
    if not ref_clean:
        return 100.0

    if HAS_JIWER:
        error = jiwer.wer(ref_clean, hyp_clean)
        return round(float(error) * 100.0, 2)

    # Pure Python Levenshtein fallback
    ref_tokens = ref_clean.split()
    hyp_tokens = hyp_clean.split()
    if not ref_tokens:
        return 100.0

    edits = levenshtein_distance(ref_tokens, hyp_tokens)
    return round((edits / len(ref_tokens)) * 100.0, 2)


def calculate_item_metrics(
    ground_truth_items: List[Dict[str, Any]],
    predicted_items: List[Dict[str, Any]]
) -> Dict[str, float]:
    """
    Calculates business-critical grocery Item-Level Precision, Recall, and F1:
    A True Positive requires matching BOTH the canonical sku_id AND normalized quantity.
    """
    gt_pairs = [
        (item.get("sku_id"), round(float(item.get("qty", item.get("quantity", 1.0))), 2))
        for item in ground_truth_items
        if item.get("sku_id")
    ]
    pred_pairs = [
        (item.get("sku_id"), round(float(item.get("qty", item.get("quantity", 1.0))), 2))
        for item in predicted_items
        if item.get("sku_id")
    ]

    tp = 0
    pred_remaining = list(pred_pairs)

    for target in gt_pairs:
        if target in pred_remaining:
            tp += 1
            pred_remaining.remove(target)

    fp = len(pred_pairs) - tp
    fn = len(gt_pairs) - tp

    precision = (tp / (tp + fp)) * 100.0 if (tp + fp) > 0 else (100.0 if len(gt_pairs) == 0 else 0.0)
    recall = (tp / (tp + fn)) * 100.0 if (tp + fn) > 0 else (100.0 if len(gt_pairs) == 0 else 0.0)
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": round(precision, 2),
        "recall": round(recall, 2),
        "item_f1": round(f1, 2)
    }


def calculate_quantity_accuracy(
    ground_truth_items: List[Dict[str, Any]],
    predicted_items: List[Dict[str, Any]]
) -> float:
    """
    Calculates the proportion of correctly extracted quantities among matched SKUs.
    """
    pred_map = {
        item.get("sku_id"): float(item.get("qty", item.get("quantity", 1.0)))
        for item in predicted_items
        if item.get("sku_id")
    }

    matched_sku_count = 0
    exact_qty_count = 0

    for gt in ground_truth_items:
        sku = gt.get("sku_id")
        if sku in pred_map:
            matched_sku_count += 1
            gt_qty = float(gt.get("qty", gt.get("quantity", 1.0)))
            if abs(gt_qty - pred_map[sku]) < 1e-3:
                exact_qty_count += 1

    if matched_sku_count == 0:
        return 0.0
    return round((exact_qty_count / matched_sku_count) * 100.0, 2)
