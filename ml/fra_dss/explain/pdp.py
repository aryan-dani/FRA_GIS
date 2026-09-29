"""Partial dependence helpers."""

from __future__ import annotations

from typing import Any

import numpy as np


def simple_pdp(model, X, feature_idx: int, grid: np.ndarray | None = None) -> dict[str, Any]:
    X = np.asarray(X, dtype=float)
    if grid is None:
        col = X[:, feature_idx]
        grid = np.linspace(np.nanpercentile(col, 5), np.nanpercentile(col, 95), 20)
    preds = []
    for v in grid:
        Xt = X.copy()
        Xt[:, feature_idx] = v
        if hasattr(model, "predict_proba"):
            preds.append(model.predict_proba(Xt).mean(axis=0).tolist())
        else:
            preds.append(model.predict(Xt).mean())
    return {"grid": grid.tolist(), "preds": preds}
