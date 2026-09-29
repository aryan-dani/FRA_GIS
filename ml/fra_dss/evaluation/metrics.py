"""Classification metrics helpers."""

from __future__ import annotations

import time
from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    brier_score_loss,
    classification_report,
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
    log_loss,
    matthews_corrcoef,
    precision_recall_fscore_support,
    roc_auc_score,
)


def multiclass_brier(y_true: np.ndarray, proba: np.ndarray, n_classes: int) -> float:
    y_onehot = np.eye(n_classes)[y_true]
    return float(np.mean(np.sum((proba - y_onehot) ** 2, axis=1)))


def evaluate_classifier(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    proba: np.ndarray | None,
    labels: list[str],
    train_seconds: float | None = None,
    infer_ms_per_1k: float | None = None,
    model_bytes: int | None = None,
) -> dict[str, Any]:
    n_classes = len(labels)
    out: dict[str, Any] = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro")),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted")),
        "mcc": float(matthews_corrcoef(y_true, y_pred)),
        "cohen_kappa": float(cohen_kappa_score(y_true, y_pred)),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }
    p, r, f, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=list(range(n_classes)), zero_division=0
    )
    out["per_class"] = {
        labels[i]: {
            "precision": float(p[i]),
            "recall": float(r[i]),
            "f1": float(f[i]),
        }
        for i in range(n_classes)
    }
    if proba is not None:
        try:
            out["log_loss"] = float(log_loss(y_true, proba, labels=list(range(n_classes))))
        except Exception:
            out["log_loss"] = None
        try:
            out["roc_auc_ovr"] = float(
                roc_auc_score(y_true, proba, multi_class="ovr", average="macro")
            )
        except Exception:
            out["roc_auc_ovr"] = None
        out["brier"] = multiclass_brier(y_true, proba, n_classes)
    if train_seconds is not None:
        out["train_seconds"] = float(train_seconds)
    if infer_ms_per_1k is not None:
        out["latency_ms_per_1k"] = float(infer_ms_per_1k)
    if model_bytes is not None:
        out["model_bytes"] = int(model_bytes)
    return out


def timed_predict_proba(model, X, n_repeat: int = 1) -> tuple[np.ndarray, float]:
    t0 = time.perf_counter()
    proba = None
    for _ in range(n_repeat):
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(X)
        else:
            pred = model.predict(X)
            n_classes = int(np.max(pred)) + 1
            proba = np.eye(n_classes)[pred]
    elapsed = time.perf_counter() - t0
    ms_per_1k = (elapsed / max(len(X), 1)) * 1000 * 1000 / n_repeat
    return proba, ms_per_1k
