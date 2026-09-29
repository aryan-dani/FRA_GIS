"""Feature engineering helpers (selection)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_classif
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder, OrdinalEncoder

from fra_dss.config import SEED


def mutual_info_ranking(df: pd.DataFrame, cols: list[str], y: np.ndarray) -> dict[str, float]:
    X = df[cols].copy()
    for c in cols:
        if X[c].dtype == object:
            X[c] = X[c].fillna("Missing").astype(str)
        else:
            X[c] = pd.to_numeric(X[c], errors="coerce").fillna(-1)
    enc = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    Xt = enc.fit_transform(X)
    mi = mutual_info_classif(Xt, y, random_state=SEED)
    return {
        c: float(v)
        for c, v in sorted(zip(cols, mi), key=lambda t: t[1], reverse=True)
    }


def l1_selected_features(
    X: np.ndarray, y: np.ndarray, feature_names: list[str], C: float = 0.1
) -> list[str]:
    clf = LogisticRegression(
        penalty="l1",
        solver="saga",
        C=C,
        max_iter=500,
        random_state=SEED,
        n_jobs=1,
    )
    clf.fit(X, y)
    coef = np.abs(clf.coef_).sum(axis=0)
    return [n for n, w in zip(feature_names, coef) if w > 1e-6]
