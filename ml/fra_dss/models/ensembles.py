"""Voting, stacking, and blending helpers."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.ensemble import StackingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from fra_dss.config import SEED, n_jobs
from fra_dss.models.zoo import build_estimator


def soft_voting(mode: str = "fast") -> VotingClassifier:
    estimators = [
        ("rf", build_estimator("random_forest", mode)),
        ("lgbm", build_estimator("lightgbm", mode)),
        ("hgb", build_estimator("hist_gradient_boosting", mode)),
    ]
    return VotingClassifier(estimators=estimators, voting="soft", n_jobs=n_jobs())


def stacking_logistic(mode: str = "fast") -> StackingClassifier:
    estimators = [
        ("rf", build_estimator("random_forest", mode)),
        ("lgbm", build_estimator("lightgbm", mode)),
        ("xgb", build_estimator("xgboost", mode)),
    ]
    return StackingClassifier(
        estimators=estimators,
        final_estimator=LogisticRegression(max_iter=400, random_state=SEED),
        cv=3,
        n_jobs=n_jobs(),
        passthrough=False,
    )


def stacking_lgbm(mode: str = "fast") -> StackingClassifier:
    from lightgbm import LGBMClassifier

    estimators = [
        ("rf", build_estimator("random_forest", mode)),
        ("hgb", build_estimator("hist_gradient_boosting", mode)),
        ("xgb", build_estimator("xgboost", mode)),
    ]
    meta = LGBMClassifier(
        n_estimators=60, max_depth=4, learning_rate=0.08, random_state=SEED, verbose=-1
    )
    return StackingClassifier(
        estimators=estimators,
        final_estimator=meta,
        cv=3,
        n_jobs=n_jobs(),
    )


def weighted_vote_from_oof(
    oof_probas: dict[str, np.ndarray],
    weights: dict[str, float] | None = None,
) -> np.ndarray:
    names = list(oof_probas.keys())
    if not weights:
        weights = {n: 1.0 / len(names) for n in names}
    total_w = sum(weights[n] for n in names)
    acc = None
    for n in names:
        w = weights[n] / total_w
        acc = oof_probas[n] * w if acc is None else acc + oof_probas[n] * w
    return acc


def blend_holdout(
    base_probas: list[np.ndarray], meta_y: np.ndarray
) -> LogisticRegression:
    X = np.hstack(base_probas)
    meta = LogisticRegression(max_iter=400, random_state=SEED)
    meta.fit(X, meta_y)
    return meta
