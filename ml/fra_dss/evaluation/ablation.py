"""Ablation helpers."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from fra_dss.config import SEED
from fra_dss.models.zoo import build_estimator
from fra_dss.preprocessing.pipelines import build_preprocessor, select_frame


def feature_set_ablation(df: pd.DataFrame, y: np.ndarray, mode: str = "fast") -> dict[str, Any]:
    results = {}
    for fs in ("A", "B"):
        X = select_frame(df, fs)
        X_tr, X_te, y_tr, y_te = train_test_split(
            X, y, test_size=0.2, random_state=SEED, stratify=y
        )
        pipe = Pipeline(
            [
                ("pre", build_preprocessor(fs)),
                ("model", build_estimator("lightgbm", mode)),
            ]
        )
        pipe.fit(X_tr, y_tr)
        pred = pipe.predict(X_te)
        results[fs] = {"macro_f1": float(f1_score(y_te, pred, average="macro"))}
    results["gap_B_minus_A"] = results["B"]["macro_f1"] - results["A"]["macro_f1"]
    results["interpretation"] = (
        "Positive gap means process-stage features lift macro-F1. "
        "That lift is partly circular because committee level and processing days "
        "are correlated with outcome."
    )
    return results
