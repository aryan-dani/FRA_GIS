"""Priority / triage scoring."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from fra_dss.config import dss_weights


def triage_score(
    reject_prob: float,
    expected_delay_days: float,
    pending_age_days: float,
) -> float:
    w = dss_weights()["weights"]
    caps = dss_weights()
    delay_n = min(expected_delay_days / float(caps["delay_cap_days"]), 1.0)
    age_n = min(pending_age_days / float(caps["pending_age_cap_days"]), 1.0)
    return float(
        100
        * (
            w["rejection_risk"] * reject_prob
            + w["expected_delay"] * delay_n
            + w["pending_age"] * age_n
        )
    )


def rank_pending(
    pending_df: pd.DataFrame,
    reject_probs: np.ndarray,
    eta_days: np.ndarray,
) -> pd.DataFrame:
    out = pending_df.copy()
    ages = pd.to_numeric(out.get("processing_days"), errors="coerce").fillna(180).to_numpy()
    scores = [
        triage_score(float(rp), float(eta), float(age))
        for rp, eta, age in zip(reject_probs, eta_days, ages)
    ]
    out["triage_score"] = scores
    out["reject_prob"] = reject_probs
    out["eta_days"] = eta_days
    return out.sort_values("triage_score", ascending=False)
