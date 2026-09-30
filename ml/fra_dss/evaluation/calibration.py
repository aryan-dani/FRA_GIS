"""Calibration helpers."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import brier_score_loss


def expected_calibration_error(
    y_true: np.ndarray, proba: np.ndarray, n_bins: int = 10
) -> float:
    """ECE for multiclass using max-prob confidence."""
    conf = proba.max(axis=1)
    pred = proba.argmax(axis=1)
    correct = (pred == y_true).astype(float)
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        m = (conf >= bins[i]) & (conf < bins[i + 1] if i < n_bins - 1 else conf <= bins[i + 1])
        if m.sum() == 0:
            continue
        ece += (m.mean()) * abs(correct[m].mean() - conf[m].mean())
    return float(ece)


def calibrate_model(estimator, X_train, y_train, method: str = "isotonic") -> Any:
    return CalibratedClassifierCV(estimator, method=method, cv=3)


def abstention_curve(
    y_true: np.ndarray, proba: np.ndarray, thresholds: list[float] | None = None
) -> list[dict[str, float]]:
    thresholds = thresholds or [0.4, 0.5, 0.55, 0.6, 0.7, 0.8]
    conf = proba.max(axis=1)
    pred = proba.argmax(axis=1)
    rows = []
    for t in thresholds:
        keep = conf >= t
        coverage = float(keep.mean())
        acc = float((pred[keep] == y_true[keep]).mean()) if keep.any() else float("nan")
        rows.append({"threshold": t, "coverage": coverage, "accuracy": acc})
    return rows
