"""Split strategies including a locked district-held-out test set."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, StratifiedKFold, train_test_split

from fra_dss.config import METRICS_DIR, SEED, ensure_dirs, experiment_config


def _district_allocation(
    df: pd.DataFrame,
    test_fraction: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Allocate whole districts to a locked test set near test_fraction of rows."""
    rng = np.random.default_rng(seed)
    districts = df.groupby("district").size().sort_values(ascending=False)
    order = districts.index.to_list()
    rng.shuffle(order)
    target = int(round(len(df) * test_fraction))
    test_districts: list[str] = []
    n_test = 0
    for d in order:
        size = int(districts[d])
        if n_test + size <= target or not test_districts:
            test_districts.append(str(d))
            n_test += size
        if n_test >= target:
            break
    test_mask = df["district"].astype(str).isin(test_districts).to_numpy()
    test_idx = np.where(test_mask)[0]
    train_idx = np.where(~test_mask)[0]
    return train_idx, test_idx


def lock_splits(df: pd.DataFrame, seed: int = SEED) -> dict[str, np.ndarray]:
    """Create and persist the locked train/test indices (once)."""
    ensure_dirs()
    split_dir = METRICS_DIR / "splits"
    train_path = split_dir / "locked_train_idx.json"
    test_path = split_dir / "locked_test_idx.json"
    cfg = experiment_config()
    frac = float(cfg["splits"]["locked_test_fraction"])

    if train_path.exists() and test_path.exists():
        train_idx = np.array(json.loads(train_path.read_text(encoding="utf-8")))
        test_idx = np.array(json.loads(test_path.read_text(encoding="utf-8")))
        # Reindex if dataframe length changed (e.g. fast subsample): rebuild
        if len(train_idx) + len(test_idx) == len(df):
            return {"train": train_idx, "test": test_idx}

    train_idx, test_idx = _district_allocation(df, frac, seed)
    train_path.write_text(json.dumps(train_idx.tolist()), encoding="utf-8")
    test_path.write_text(json.dumps(test_idx.tolist()), encoding="utf-8")
    meta = {
        "n_train": int(len(train_idx)),
        "n_test": int(len(test_idx)),
        "test_fraction": float(len(test_idx) / len(df)),
        "train_districts": sorted(df.iloc[train_idx]["district"].astype(str).unique().tolist()),
        "test_districts": sorted(df.iloc[test_idx]["district"].astype(str).unique().tolist()),
        "overlap_districts": [],
        "seed": seed,
    }
    overlap = set(meta["train_districts"]) & set(meta["test_districts"])
    meta["overlap_districts"] = sorted(overlap)
    (split_dir / "locked_split_meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )
    return {"train": train_idx, "test": test_idx}


def iter_s1(
    df: pd.DataFrame,
    y: np.ndarray,
    groups: np.ndarray,
    n_splits: int | None = None,
) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    """Grouped K-fold by district (primary S1)."""
    cfg = experiment_config()
    folds = n_splits or int(cfg["splits"]["s1_folds"])
    # StratifiedGroupKFold needs sklearn >= 1.0; fall back to GroupKFold
    try:
        from sklearn.model_selection import StratifiedGroupKFold

        cv = StratifiedGroupKFold(n_splits=folds, shuffle=True, random_state=SEED)
        yield from cv.split(df, y, groups)
    except Exception:
        cv = GroupKFold(n_splits=folds)
        yield from cv.split(df, y, groups)


def iter_s2(y: np.ndarray, n_splits: int = 5) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    """Random stratified K-fold (optimistic baseline)."""
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=SEED)
    X_dummy = np.zeros(len(y))
    yield from cv.split(X_dummy, y)


def temporal_mask(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    cfg = experiment_config()
    max_year = int(cfg["splits"]["temporal_train_max_year"])
    year = pd.to_numeric(df["year_filed"], errors="coerce").fillna(2015).astype(int)
    train = np.where(year.to_numpy() <= max_year)[0]
    test = np.where(year.to_numpy() > max_year)[0]
    return train, test


def leave_one_state_out(df: pd.DataFrame) -> Iterator[tuple[str, np.ndarray, np.ndarray]]:
    states = sorted(df["state"].astype(str).unique())
    for state in states:
        test = np.where(df["state"].astype(str).to_numpy() == state)[0]
        train = np.where(df["state"].astype(str).to_numpy() != state)[0]
        yield state, train, test


def random_holdout(
    y: np.ndarray, test_size: float = 0.2, seed: int = SEED
) -> tuple[np.ndarray, np.ndarray]:
    idx = np.arange(len(y))
    train, test = train_test_split(
        idx, test_size=test_size, random_state=seed, stratify=y
    )
    return train, test
