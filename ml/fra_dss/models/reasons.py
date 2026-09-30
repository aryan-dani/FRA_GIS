"""Rejection-reason classifier (T2) and resolved-outcome binary (T1b)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, top_k_accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

from fra_dss.config import SEED
from fra_dss.models.zoo import build_estimator
from fra_dss.preprocessing.pipelines import build_preprocessor, select_frame


def train_rejection_reasons(df: pd.DataFrame, mode: str = "fast") -> dict[str, Any]:
    rejected = df[df["status"].astype(str) == "Rejected"].copy()
    rejected = rejected[rejected["rejection_reason"].notna()]
    y_raw = rejected["rejection_reason"].astype(str)
    le = LabelEncoder()
    y = le.fit_transform(y_raw)
    X = select_frame(rejected, "A")
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=SEED, stratify=y
    )
    results = {}
    best = None
    best_f1 = -1.0
    best_pipe = None
    for name in ("logistic_l2", "random_forest", "lightgbm", "xgboost"):
        try:
            est = build_estimator(name, mode)
            pipe = Pipeline([("pre", build_preprocessor("A")), ("model", est)])
            pipe.fit(X_tr, y_tr)
            proba = pipe.predict_proba(X_te)
            pred = np.argmax(proba, axis=1)
            macro = float(f1_score(y_te, pred, average="macro"))
            top3 = float(top_k_accuracy_score(y_te, proba, k=min(3, proba.shape[1])))
            results[name] = {"macro_f1": macro, "top3_accuracy": top3}
            if macro > best_f1:
                best_f1 = macro
                best = name
                best_pipe = pipe
        except Exception as exc:
            results[name] = {"error": str(exc)}
    return {
        "metrics": results,
        "champion": best,
        "label_encoder": le,
        "model": best_pipe,
        "classes": list(le.classes_),
        "note": (
            "Some reasons may be recoverable from fields (e.g. applicant_type). "
            "This is expected on synthetic data."
        ),
    }


def train_resolved_binary(df: pd.DataFrame, mode: str = "fast") -> dict[str, Any]:
    resolved = df[df["status"].astype(str).isin(["Approved", "Rejected"])].copy()
    y = (resolved["status"].astype(str) == "Rejected").astype(int).to_numpy()
    X = select_frame(resolved, "A")
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=SEED, stratify=y
    )
    results = {}
    best = None
    best_f1 = -1.0
    best_pipe = None
    for name in ("logistic_l2", "random_forest", "lightgbm", "xgboost"):
        try:
            est = build_estimator(name, mode)
            pipe = Pipeline([("pre", build_preprocessor("A")), ("model", est)])
            pipe.fit(X_tr, y_tr)
            pred = pipe.predict(X_te)
            macro = float(f1_score(y_te, pred, average="macro"))
            acc = float(accuracy_score(y_te, pred))
            results[name] = {"macro_f1": macro, "accuracy": acc}
            if macro > best_f1:
                best_f1 = macro
                best = name
                best_pipe = pipe
        except Exception as exc:
            results[name] = {"error": str(exc)}
    return {
        "metrics": results,
        "champion": best,
        "model": best_pipe,
        "positive_class": "Rejected",
    }
