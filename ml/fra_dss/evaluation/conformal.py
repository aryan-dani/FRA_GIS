"""Simple inductive conformal prediction sets for multiclass (stretch)."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

from fra_dss.config import METRICS_DIR, SEED, ensure_dirs, mode_settings
from fra_dss.data.load import load_claims, write_json
from fra_dss.models.zoo import build_estimator
from fra_dss.preprocessing.pipelines import build_preprocessor, select_frame

STATUS_LABELS = ["Approved", "Pending", "Rejected"]


def run_conformal(mode: str = "fast", alpha: float = 0.1) -> dict[str, Any]:
    """
    Split-conformal with APS-style scores using 1 - P(y).
    Target coverage about 1 - alpha on the locked holdout-style test slice.
    """
    ensure_dirs()
    df = load_claims(mode=mode)
    le = LabelEncoder()
    le.fit(STATUS_LABELS)
    y = le.transform(df["status"].astype(str))
    X = select_frame(df, "A")

    X_tr, X_tmp, y_tr, y_tmp = train_test_split(
        X, y, test_size=0.4, random_state=SEED, stratify=y
    )
    X_cal, X_te, y_cal, y_te = train_test_split(
        X_tmp, y_tmp, test_size=0.5, random_state=SEED, stratify=y_tmp
    )

    pipe = Pipeline(
        [
            ("pre", build_preprocessor("A")),
            ("model", build_estimator("lightgbm", mode)),
        ]
    )
    pipe.fit(X_tr, y_tr)
    proba_cal = pipe.predict_proba(X_cal)
    # Nonconformity: 1 - probability of true class
    scores = 1.0 - proba_cal[np.arange(len(y_cal)), y_cal]
    q_level = np.ceil((len(scores) + 1) * (1 - alpha)) / len(scores)
    q_level = min(q_level, 1.0)
    qhat = float(np.quantile(scores, q_level, method="higher"))

    proba_te = pipe.predict_proba(X_te)
    sets = []
    covered = 0
    sizes = []
    for i, yt in enumerate(y_te):
        s = set(np.where(1.0 - proba_te[i] <= qhat)[0].tolist())
        if not s:
            s = {int(np.argmax(proba_te[i]))}
        sets.append(sorted(s))
        sizes.append(len(s))
        if int(yt) in s:
            covered += 1

    report = {
        "method": "split-conformal (1 - P(y) scores)",
        "alpha": alpha,
        "target_coverage": 1 - alpha,
        "empirical_coverage": float(covered / len(y_te)),
        "mean_set_size": float(np.mean(sizes)),
        "median_set_size": float(np.median(sizes)),
        "qhat": qhat,
        "n_train": int(len(X_tr)),
        "n_cal": int(len(X_cal)),
        "n_test": int(len(X_te)),
        "model": "lightgbm",
        "feature_set": "A",
        "synthetic": True,
        "caveat": (
            "Conformal sets are calibrated on synthetic data. Coverage on real claims is unknown."
        ),
    }
    write_json(METRICS_DIR / "conformal.json", report)
    return report


if __name__ == "__main__":
    print(run_conformal())
