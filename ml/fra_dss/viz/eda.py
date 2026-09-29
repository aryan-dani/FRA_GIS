"""EDA figure generators."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from fra_dss.config import FIGURES_DIR, ensure_dirs
from fra_dss.viz.style import apply_style, PALETTE


def save_target_balance(df: pd.DataFrame) -> Path:
    ensure_dirs()
    apply_style()
    fig, ax = plt.subplots(figsize=(6, 4))
    counts = df["status"].value_counts()
    counts.plot(kind="bar", ax=ax, color=PALETTE[: len(counts)])
    ax.set_title("Figure 1. Claim status balance (synthetic)")
    ax.set_xlabel("Status")
    ax.set_ylabel("Count")
    fig.tight_layout()
    path = FIGURES_DIR / "01_status_balance.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def save_status_by_state(df: pd.DataFrame) -> Path:
    ensure_dirs()
    apply_style()
    ct = pd.crosstab(df["state"], df["status"], normalize="index")
    fig, ax = plt.subplots(figsize=(8, 4))
    ct.plot(kind="bar", stacked=True, ax=ax, color=PALETTE[: ct.shape[1]])
    ax.set_title("Figure 2. Status share by state (synthetic)")
    ax.set_ylabel("Share")
    ax.legend(title="Status", bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.tight_layout()
    path = FIGURES_DIR / "02_status_by_state.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def save_temporal_drift(df: pd.DataFrame) -> Path:
    ensure_dirs()
    apply_style()
    year = pd.to_numeric(df["year_filed"], errors="coerce")
    tmp = df.copy()
    tmp["year_filed"] = year
    pivot = (
        tmp.groupby(["year_filed", "status"]).size().unstack(fill_value=0)
    )
    share = pivot.div(pivot.sum(axis=1), axis=0)
    fig, ax = plt.subplots(figsize=(8, 4))
    share.plot(ax=ax, color=PALETTE[: share.shape[1]])
    ax.set_title("Figure 3. Temporal drift of status shares (synthetic)")
    ax.set_xlabel("Year filed")
    ax.set_ylabel("Share")
    fig.tight_layout()
    path = FIGURES_DIR / "03_temporal_drift.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def save_land_skew(df: pd.DataFrame) -> Path:
    ensure_dirs()
    apply_style()
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    land = pd.to_numeric(df["land_area_ha"], errors="coerce").dropna()
    axes[0].hist(land.clip(upper=land.quantile(0.99)), bins=40, color=PALETTE[0])
    axes[0].set_title("Land area (clipped 99th pct)")
    axes[0].set_xlabel("ha")
    axes[1].hist(np_log1p(land), bins=40, color=PALETTE[1])
    axes[1].set_title("log1p(land area)")
    axes[1].set_xlabel("log1p(ha)")
    fig.suptitle("Figure 4. Land area skew (synthetic)")
    fig.tight_layout()
    path = FIGURES_DIR / "04_land_area_skew.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def np_log1p(s):
    import numpy as np

    return np.log1p(s.clip(lower=0))


def save_docs_reject(df: pd.DataFrame) -> Path:
    ensure_dirs()
    apply_style()
    ct = pd.crosstab(df["documentation_completeness"], df["status"], normalize="index")
    fig, ax = plt.subplots(figsize=(7, 4))
    ct.plot(kind="bar", ax=ax, color=PALETTE[: ct.shape[1]])
    ax.set_title("Figure 5. Status by documentation completeness (synthetic)")
    ax.set_ylabel("Share")
    fig.tight_layout()
    path = FIGURES_DIR / "05_docs_vs_status.png"
    fig.savefig(path)
    plt.close(fig)
    return path
