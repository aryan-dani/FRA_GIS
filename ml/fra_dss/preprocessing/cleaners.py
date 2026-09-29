"""Column cleaners and rare-level grouping."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


class ColumnCleaner(BaseEstimator, TransformerMixin):
    """Strip whitespace, fill NA for known categoricals, coerce numerics."""

    def __init__(self, feature_set: str = "A"):
        self.feature_set = feature_set

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        df = X.copy() if isinstance(X, pd.DataFrame) else pd.DataFrame(X)
        for col in df.select_dtypes(include=["object", "string"]).columns:
            df[col] = df[col].fillna("Unknown").astype(str).str.strip()
        for col in ("land_area_ha", "year_filed", "processing_days", "latitude", "longitude"):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        if "land_area_ha" in df.columns:
            df["land_area_ha"] = df["land_area_ha"].fillna(df["land_area_ha"].median() if df["land_area_ha"].notna().any() else 1.0)
        if "year_filed" in df.columns:
            df["year_filed"] = df["year_filed"].fillna(2015)
        if "processing_days" in df.columns:
            df["processing_days"] = df["processing_days"].fillna(180)
        return df


class RareLevelGrouper(BaseEstimator, TransformerMixin):
    """Group rare claim_type levels for linear and distance models."""

    def __init__(self, column: str = "claim_type", min_count: int = 500, other: str = "other"):
        self.column = column
        self.min_count = min_count
        self.other = other
        self.keep_levels_: set[str] = set()

    def fit(self, X, y=None):
        series = X[self.column].astype(str)
        counts = series.value_counts()
        self.keep_levels_ = set(counts[counts >= self.min_count].index.tolist())
        return self

    def transform(self, X):
        df = X.copy()
        df[self.column] = df[self.column].astype(str).where(
            df[self.column].astype(str).isin(self.keep_levels_), self.other
        )
        return df


class Winsorizer(BaseEstimator, TransformerMixin):
    def __init__(self, columns: list[str] | None = None, lower: float = 0.01, upper: float = 0.99):
        self.columns = columns or ["land_area_ha"]
        self.lower = lower
        self.upper = upper
        self.bounds_: dict[str, tuple[float, float]] = {}

    def fit(self, X, y=None):
        df = X if isinstance(X, pd.DataFrame) else pd.DataFrame(X)
        for col in self.columns:
            if col in df.columns:
                s = pd.to_numeric(df[col], errors="coerce")
                self.bounds_[col] = (float(s.quantile(self.lower)), float(s.quantile(self.upper)))
        return self

    def transform(self, X):
        df = X.copy() if isinstance(X, pd.DataFrame) else pd.DataFrame(X)
        for col, (lo, hi) in self.bounds_.items():
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").clip(lo, hi)
        return df
