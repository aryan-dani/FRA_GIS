"""Custom sklearn transformers for engineered features."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

from fra_dss.config import experiment_config


class FeatureEngineer(BaseEstimator, TransformerMixin):
    """Add filing-time engineered columns. Fit only uses training rows."""

    def __init__(self, reference_year: int | None = None, include_district_stats: bool = True):
        cfg = experiment_config()
        self.reference_year = reference_year or int(cfg.get("reference_year", 2024))
        self.include_district_stats = include_district_stats
        self.district_stats_: dict[str, dict[str, float]] = {}
        self.state_year_pending_: dict[tuple[str, int], float] = {}
        self.global_pending_rate_: float = 0.3

    def fit(self, X, y=None):
        df = X.copy() if isinstance(X, pd.DataFrame) else pd.DataFrame(X)
        if y is not None and self.include_district_stats:
            tmp = df.copy()
            tmp["_y"] = np.asarray(y)
            # y may be encoded ints; store approval rate when labels available as strings later
            if tmp["_y"].dtype == object:
                approved = (tmp["_y"].astype(str) == "Approved").astype(float)
            else:
                # Prefer label 0 = Approved if LabelEncoder fitted on STATUS_LABELS order
                approved = (tmp["_y"] == 0).astype(float)
            pending = (
                (tmp["_y"].astype(str) == "Pending").astype(float)
                if tmp["_y"].dtype == object
                else (tmp["_y"] == 1).astype(float)
            )
            for district, g in tmp.groupby(tmp["district"].astype(str)):
                self.district_stats_[str(district)] = {
                    "approval_rate": float(approved.loc[g.index].mean()),
                    "mean_land": float(pd.to_numeric(g["land_area_ha"], errors="coerce").mean()),
                }
            self.global_pending_rate_ = float(pending.mean())
            if "year_filed" in tmp.columns:
                for (state, year), g in tmp.groupby(
                    [tmp["state"].astype(str), pd.to_numeric(tmp["year_filed"], errors="coerce").fillna(2015).astype(int)]
                ):
                    self.state_year_pending_[(str(state), int(year))] = float(
                        pending.loc[g.index].mean()
                    )
        return self

    def transform(self, X):
        df = X.copy() if isinstance(X, pd.DataFrame) else pd.DataFrame(X)
        year = pd.to_numeric(df.get("year_filed"), errors="coerce").fillna(2015)
        land = pd.to_numeric(df.get("land_area_ha"), errors="coerce").fillna(1.0)
        df["claim_age"] = self.reference_year - year
        df["log_land_area"] = np.log1p(land.clip(lower=0))
        df["pre_2019_flag"] = (year < 2019).astype(int)
        df["is_rare_claim_type"] = (
            ~df["claim_type"].astype(str).isin(["IFR", "CFR", "CR"])
        ).astype(int)
        docs = df["documentation_completeness"].astype(str)
        gs = df["gram_sabha_resolution"].astype(str)
        df["docs_x_gramsabha"] = (
            (docs == "Complete").astype(int) * (gs == "Passed").astype(int)
        )
        # land bins
        df["land_bin"] = pd.cut(
            land,
            bins=[-0.01, 1.0, 2.0, 5.0, 20.0, 1e9],
            labels=["tiny", "small", "medium", "large", "huge"],
        ).astype(str)

        if self.include_district_stats:
            rates = []
            lands = []
            for d in df["district"].astype(str):
                stats = self.district_stats_.get(d)
                if stats:
                    rates.append(stats["approval_rate"])
                    lands.append(stats["mean_land"])
                else:
                    rates.append(0.46)
                    lands.append(1.43)
            df["district_oof_approval"] = rates
            df["district_mean_land"] = lands
            backlog = []
            for state, yr in zip(df["state"].astype(str), year.astype(int)):
                backlog.append(
                    self.state_year_pending_.get((state, int(yr)), self.global_pending_rate_)
                )
            df["state_year_backlog"] = backlog
        return df
