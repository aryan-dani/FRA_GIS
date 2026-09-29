"""Leakage audit for feature sets A, B, C."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_classif
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import LabelEncoder, OrdinalEncoder
from sklearn.tree import DecisionTreeClassifier

from fra_dss.config import METRICS_DIR, SEED, experiment_config

FORBIDDEN = {
    "rejection_reason",
    "claim_id",
    "status",
    "village",
    "adjacent_forest_area",
}

PROCESS_LEAKY = {"committee_level_reached", "processing_days"}


def _encode_frame(df: pd.DataFrame, cols: list[str]) -> np.ndarray:
    X = df[cols].copy()
    for c in cols:
        if X[c].dtype == object or str(X[c].dtype) == "string":
            X[c] = X[c].fillna("Missing").astype(str)
        else:
            X[c] = pd.to_numeric(X[c], errors="coerce").fillna(-1)
    enc = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    return enc.fit_transform(X)


def audit_leakage(df: pd.DataFrame) -> dict[str, Any]:
    cfg = experiment_config()
    y = LabelEncoder().fit_transform(df["status"].astype(str))
    candidate_cols = [c for c in df.columns if c not in {"status", "claim_id"}]

    single_feature: dict[str, float] = {}
    for col in candidate_cols:
        try:
            X = _encode_frame(df, [col])
            clf = DecisionTreeClassifier(max_depth=4, random_state=SEED)
            scores = cross_val_score(clf, X, y, cv=3, scoring="f1_macro")
            single_feature[col] = float(np.mean(scores))
        except Exception:
            single_feature[col] = float("nan")

    sample = df.sample(n=min(8000, len(df)), random_state=SEED)
    y_s = LabelEncoder().fit_transform(sample["status"].astype(str))
    mi_cols = [c for c in candidate_cols if c in sample.columns]
    X_mi = _encode_frame(sample, mi_cols)
    mi = mutual_info_classif(X_mi, y_s, random_state=SEED)
    mi_rank = {
        col: float(val)
        for col, val in sorted(zip(mi_cols, mi), key=lambda t: t[1], reverse=True)
    }

    set_checks: dict[str, Any] = {}
    for name, spec in cfg["feature_sets"].items():
        cols = list(spec["columns"])
        forbidden_hit = sorted(set(cols) & FORBIDDEN)
        process_hit = sorted(set(cols) & PROCESS_LEAKY)
        set_checks[name] = {
            "columns": cols,
            "forbidden_present": forbidden_hit,
            "process_features_present": process_hit,
            "pass": len(forbidden_hit) == 0,
            "notes": spec.get("description", ""),
        }

    rr_score = single_feature.get("rejection_reason")
    report = {
        "synthetic": True,
        "single_feature_macro_f1": single_feature,
        "mutual_information": mi_rank,
        "feature_set_checks": set_checks,
        "rejection_reason_probe": {
            "column": "rejection_reason",
            "single_feature_macro_f1": rr_score,
            "allowed_in_set_A": False,
            "allowed_in_set_B": False,
            "reason": (
                "Non-null only when status is Rejected: perfect target leakage for status."
            ),
        },
        "process_leakage_note": (
            "committee_level_reached and processing_days are partly consequences of "
            "outcome. Set B is process-aware and documented as partly circular."
        ),
    }
    path = METRICS_DIR / "leakage_audit.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
