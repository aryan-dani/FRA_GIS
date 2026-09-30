"""SHAP helpers."""

from __future__ import annotations

from typing import Any

import numpy as np


def tree_shap_top(model, X, feature_names: list[str], pred_idx: int, top_k: int = 5):
    import shap

    explainer = shap.TreeExplainer(model)
    values = explainer.shap_values(X)
    if isinstance(values, list):
        arr = np.asarray(values[pred_idx])
    else:
        arr = np.asarray(values)
        if arr.ndim == 3:
            arr = arr[:, :, pred_idx]
    row = arr[0] if arr.ndim == 2 else arr.ravel()
    pairs = sorted(
        zip(feature_names, [float(np.asarray(v).reshape(-1)[0]) for v in row]),
        key=lambda t: abs(t[1]),
        reverse=True,
    )[:top_k]
    return [{"feature": n, "impact": v} for n, v in pairs]
