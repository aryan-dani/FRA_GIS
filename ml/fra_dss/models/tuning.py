"""Optuna tuning helpers."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import f1_score
from sklearn.model_selection import cross_val_score

from fra_dss.config import SEED, mode_settings, n_jobs


def tune_lightgbm(X, y, groups, mode: str = "fast") -> dict[str, Any]:
    try:
        import optuna
        from lightgbm import LGBMClassifier
        from sklearn.model_selection import GroupKFold
    except ImportError:
        return {"skipped": True, "reason": "optuna or lightgbm missing"}

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    n_trials = int(mode_settings(mode).get("n_trials", 8))
    # subsample for speed
    if len(X) > 12000:
        rng = np.random.default_rng(SEED)
        idx = rng.choice(len(X), size=12000, replace=False)
        X, y = X[idx], y[idx]
        groups = np.asarray(groups)[idx]

    def objective(trial: optuna.Trial) -> float:
        params = {
            "n_estimators": trial.suggest_categorical("n_estimators", [80, 120, 200]),
            "max_depth": trial.suggest_int("max_depth", 4, 8),
            "learning_rate": trial.suggest_float("learning_rate", 0.03, 0.15, log=True),
            "num_leaves": trial.suggest_categorical("num_leaves", [15, 31, 63]),
            "class_weight": "balanced",
            "random_state": SEED,
            "n_jobs": n_jobs(),
            "verbose": -1,
        }
        clf = LGBMClassifier(**params)
        cv = GroupKFold(n_splits=3)
        scores = cross_val_score(clf, X, y, cv=cv, groups=groups, scoring="f1_macro")
        return float(scores.mean())

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=SEED))
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    return {
        "best_params": study.best_params,
        "best_value": float(study.best_value),
        "n_trials": n_trials,
    }
