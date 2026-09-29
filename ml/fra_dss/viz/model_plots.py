"""Model comparison plots."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from fra_dss.config import FIGURES_DIR, ensure_dirs
from fra_dss.viz.style import apply_style, PALETTE


def save_leaderboard(bench: pd.DataFrame) -> Path:
    ensure_dirs()
    apply_style()
    a = bench[(bench["feature_set"] == "A") & bench["s1_macro_f1_mean"].notna()].copy()
    a = a.sort_values("s1_macro_f1_mean", ascending=True)
    fig, ax = plt.subplots(figsize=(8, max(4, 0.35 * len(a))))
    ax.barh(
        a["model"],
        a["s1_macro_f1_mean"],
        xerr=a["s1_macro_f1_std"].fillna(0),
        color=PALETTE[0],
    )
    ax.set_xlabel("Macro-F1 (S1 mean +/- std)")
    ax.set_title("Figure 10. Model leaderboard Set A (synthetic)")
    fig.tight_layout()
    path = FIGURES_DIR / "10_leaderboard_set_a.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def save_feature_set_gap(bench: pd.DataFrame) -> Path:
    ensure_dirs()
    apply_style()
    pivot = bench.pivot_table(
        index="model", columns="feature_set", values="s1_macro_f1_mean"
    )
    if "A" in pivot.columns and "B" in pivot.columns:
        gap = (pivot["B"] - pivot["A"]).dropna().sort_values()
        fig, ax = plt.subplots(figsize=(8, max(4, 0.35 * len(gap))))
        ax.barh(gap.index, gap.values, color=PALETTE[2])
        ax.axvline(0, color="black", lw=0.8)
        ax.set_xlabel("Macro-F1 gap (B minus A)")
        ax.set_title("Figure 11. Process-aware lift (partly circular)")
        fig.tight_layout()
        path = FIGURES_DIR / "11_feature_set_gap.png"
        fig.savefig(path)
        plt.close(fig)
        return path
    path = FIGURES_DIR / "11_feature_set_gap.png"
    fig, ax = plt.subplots()
    ax.text(0.5, 0.5, "Gap unavailable", ha="center")
    fig.savefig(path)
    plt.close(fig)
    return path


def save_pipeline_diagram(steps: list[str]) -> Path:
    ensure_dirs()
    apply_style()
    fig, ax = plt.subplots(figsize=(8, 0.6 * len(steps) + 1))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, len(steps) + 1)
    ax.axis("off")
    for i, step in enumerate(reversed(steps)):
        y = i + 1
        ax.add_patch(
            plt.Rectangle((0.2, y - 0.3), 0.6, 0.55, fill=True, color=PALETTE[i % len(PALETTE)], alpha=0.35)
        )
        ax.text(0.5, y, step, ha="center", va="center", fontsize=11)
        if i < len(steps) - 1:
            ax.annotate("", xy=(0.5, y + 0.35), xytext=(0.5, y + 0.7), arrowprops=dict(arrowstyle="->"))
    ax.set_title("Figure 6. Preprocessing pipeline (Set A)")
    path = FIGURES_DIR / "06_pipeline_diagram.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def save_confusion(cm: list[list[int]], labels: list[str], name: str = "champion") -> Path:
    ensure_dirs()
    apply_style()
    arr = np.asarray(cm)
    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(arr, cmap="Blues")
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticklabels(labels)
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            ax.text(j, i, int(arr[i, j]), ha="center", va="center")
    ax.set_title(f"Figure 12. Confusion matrix ({name}, synthetic)")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout()
    path = FIGURES_DIR / f"12_confusion_{name}.png"
    fig.savefig(path)
    plt.close(fig)
    return path
