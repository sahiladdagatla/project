"""
Evaluation Metrics for Satellite Flood Segmentation.

Computes:
- Flood-Class Intersection-over-Union (IoU) (Primary Sen1Floods11 benchmark metric)
- Precision, Recall, and F1-score
- Explicit exclusion of invalid / no-data pixels (-1).
"""

from typing import Dict
import numpy as np


def compute_segmentation_metrics(
    y_true: np.ndarray,
    y_pred_binary: np.ndarray
) -> Dict[str, float]:
    """
    Computes flood-class evaluation metrics against ground truth.
    y_true values:
      -1 : Invalid / No Data (masked out)
       0 : Non-water / Land
       1 : Water / Flood
    y_pred_binary values:
       0 : Predicted non-water
       1 : Predicted water
    """
    y_true = np.asarray(y_true).flatten()
    y_pred = np.asarray(y_pred_binary).flatten()

    # Filter out invalid (-1) pixels
    valid_mask = (y_true != -1)
    if not np.any(valid_mask):
        return {
            "flood_iou": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "valid_pixels_count": 0
        }

    yt = y_true[valid_mask]
    yp = y_pred[valid_mask]

    # True positives, False positives, False negatives for class 1 (Water)
    tp = np.sum((yt == 1) & (yp == 1))
    fp = np.sum((yt == 0) & (yp == 1))
    fn = np.sum((yt == 1) & (yp == 0))
    tn = np.sum((yt == 0) & (yp == 0))

    # Flood IoU = TP / (TP + FP + FN)
    union = tp + fp + fn
    flood_iou = float(tp / union) if union > 0 else 0.0

    precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    f1 = float(2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return {
        "flood_iou": round(flood_iou, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "valid_pixels_count": int(np.sum(valid_mask)),
        "water_pixels_true": int(np.sum(yt == 1)),
        "water_pixels_pred": int(np.sum(yp == 1))
    }
