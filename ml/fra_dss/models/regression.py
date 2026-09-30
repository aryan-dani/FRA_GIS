"""ETA / processing-days regression on resolved claims."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import (
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    HistGradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from fra_dss.config import SEED, n_jobs
from fra_dss.preprocessing.pipelines import build_preprocessor, select_frame


def resolved_mask(df: pd.DataFrame) -> np.ndarray:
    return df["status"].astype(str).isin(["Approved", "Rejected"]).to_numpy()


def train_eta_models(df: pd.DataFrame, mode: str = "fast") -> dict[str, Any]:
    """Train ETA regressors on Approved/Rejected only (Pending may be censored)."""
    mask = resolved_mask(df)
    sub = df.loc[mask].copy()
    y = np.log1p(pd.to_numeric(sub["processing_days"], errors="coerce").fillna(180).clip(lower=0))
    X = select_frame(sub, "A")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=SEED
    )

    models: dict[str, Any] = {
        "ridge": Ridge(alpha=1.0),
        "random_forest": RandomForestRegressor(
            n_estimators=80 if mode == "fast" else 150, random_state=SEED, n_jobs=n_jobs()
        ),
        "extra_trees": ExtraTreesRegressor(
            n_estimators=80 if mode == "fast" else 150, random_state=SEED, n_jobs=n_jobs()
        ),
        "hist_gb": HistGradientBoostingRegressor(
            max_iter=80 if mode == "fast" else 150, random_state=SEED
        ),
        "gbr": GradientBoostingRegressor(
            n_estimators=60 if mode == "fast" else 100, random_state=SEED
        ),
    }
    try:
        from lightgbm import LGBMRegressor

        models["lightgbm"] = LGBMRegressor(
            n_estimators=100, random_state=SEED, verbose=-1, n_jobs=n_jobs()
        )
    except ImportError:
        pass
    try:
        from xgboost import XGBRegressor

        models["xgboost"] = XGBRegressor(
            n_estimators=100, random_state=SEED, n_jobs=n_jobs(), tree_method="hist"
        )
    except ImportError:
        pass

    results = {}
    best_name = None
    best_mae = 1e18
    best_pipe = None
    for name, est in models.items():
        pipe = Pipeline(
            [
                ("pre", build_preprocessor("A", for_trees=name not in {"ridge"})),
                ("model", est),
            ]
        )
        pipe.fit(X_train, y_train)
        pred = np.expm1(pipe.predict(X_test))
        y_true = np.expm1(y_test)
        mae = float(mean_absolute_error(y_true, pred))
        rmse = float(np.sqrt(mean_squared_error(y_true, pred)))
        medae = float(np.median(np.abs(y_true - pred)))
        r2 = float(r2_score(y_true, pred))
        results[name] = {"mae": mae, "rmse": rmse, "median_ae": medae, "r2": r2}
        if mae < best_mae:
            best_mae = mae
            best_name = name
            best_pipe = pipe

    return {
        "caveat": (
            "ETA trained on Approved and Rejected only. Pending processing_days "
            "may be right-censored (time waited so far)."
        ),
        "metrics": results,
        "champion": best_name,
        "model": best_pipe,
    }
