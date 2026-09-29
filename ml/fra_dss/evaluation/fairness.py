"""Fairness audit on synthetic data (monitoring exercise)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, recall_score


def group_performance(
    df: pd.DataFrame,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    group_col: str,
    reject_idx: int = 2,
) -> dict[str, Any]:
    out = {}
    for g, idx in df.groupby(df[group_col].astype(str)).groups.items():
        ii = np.asarray(list(idx))
        # map to positional if needed
        if ii.max() >= len(y_true):
            continue
        yt, yp = y_true[ii], y_pred[ii]
        out[str(g)] = {
            "n": int(len(ii)),
            "macro_f1": float(f1_score(yt, yp, average="macro")),
            "reject_rate_pred": float((yp == reject_idx).mean()),
            "reject_rate_true": float((yt == reject_idx).mean()),
        }
    return out


def fairness_report(
    df: pd.DataFrame, y_true: np.ndarray, y_pred: np.ndarray
) -> dict[str, Any]:
    report = {
        "synthetic": True,
        "framing": (
            "Monitoring exercise on synthetic data. Must not automate real rejections."
        ),
        "by_state": group_performance(df, y_true, y_pred, "state"),
        "by_applicant_type": group_performance(df, y_true, y_pred, "applicant_type"),
        "by_claim_type": group_performance(df, y_true, y_pred, "claim_type"),
        "by_forest_density": group_performance(df, y_true, y_pred, "forest_density_class"),
    }
    try:
        from fairlearn.metrics import (
            demographic_parity_difference,
            equalized_odds_difference,
        )

        # Binary reject vs not for fairlearn demos
        y_bin = (y_true == 2).astype(int)
        p_bin = (y_pred == 2).astype(int)
        sens = df["applicant_type"].astype(str).to_numpy()
        report["demographic_parity_diff_reject"] = float(
            demographic_parity_difference(y_bin, p_bin, sensitive_features=sens)
        )
        report["equalized_odds_diff_reject"] = float(
            equalized_odds_difference(y_bin, p_bin, sensitive_features=sens)
        )
    except Exception as exc:
        report["fairlearn_error"] = str(exc)
    return report
