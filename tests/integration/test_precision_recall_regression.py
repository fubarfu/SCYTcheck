"""SC-007 precision/recall regression gate for hotpath optimization.

Compares candidate gating decisions against baseline decisions over synthetic
fixture pairs. Precision and recall must remain exactly equal.
"""

from __future__ import annotations

import cv2
import numpy as np

from tests.fixtures.gating_frames import FIXTURE_PAIRS


def _baseline_decision(prev_crop: np.ndarray, curr_crop: np.ndarray, threshold: float) -> str:
    if prev_crop.shape != curr_crop.shape or prev_crop.size == 0:
        return "execute_ocr"
    pixel_diff = np.mean(np.abs(prev_crop.astype(float) - curr_crop.astype(float))) / 255.0
    return "skip_ocr" if pixel_diff < threshold else "execute_ocr"


def _candidate_decision(prev_crop: np.ndarray, curr_crop: np.ndarray, threshold: float) -> str:
    if prev_crop.shape != curr_crop.shape or prev_crop.size == 0:
        return "execute_ocr"
    pixel_diff = cv2.mean(cv2.absdiff(prev_crop, curr_crop))[0] / 255.0
    return "skip_ocr" if pixel_diff < threshold else "execute_ocr"


def _precision_recall(y_true: list[str], y_pred: list[str], positive: str = "execute_ocr") -> tuple[float, float]:
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == positive and p == positive)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t != positive and p == positive)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == positive and p != positive)

    precision = 1.0 if (tp + fp) == 0 else tp / (tp + fp)
    recall = 1.0 if (tp + fn) == 0 else tp / (tp + fn)
    return precision, recall


def test_precision_recall_regression_sc007():
    """SC-007: candidate precision/recall must equal baseline on synthetic fixtures."""
    threshold = 0.10
    y_true: list[str] = []
    y_pred: list[str] = []

    for fixture_name, factory in FIXTURE_PAIRS.items():
        prev_crop, curr_crop = factory()
        baseline = _baseline_decision(prev_crop, curr_crop, threshold)
        candidate = _candidate_decision(prev_crop, curr_crop, threshold)
        y_true.append(baseline)
        y_pred.append(candidate)

    baseline_precision, baseline_recall = _precision_recall(y_true, y_true)
    candidate_precision, candidate_recall = _precision_recall(y_true, y_pred)

    assert candidate_precision == baseline_precision, (
        f"Precision drift detected: baseline={baseline_precision:.6f} candidate={candidate_precision:.6f}"
    )
    assert candidate_recall == baseline_recall, (
        f"Recall drift detected: baseline={baseline_recall:.6f} candidate={candidate_recall:.6f}"
    )
