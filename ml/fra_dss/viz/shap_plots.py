"""SHAP plot stubs (figures generated when models available)."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from fra_dss.config import FIGURES_DIR, ensure_dirs
from fra_dss.viz.style import apply_style, PALETTE


def save_shap_bar(pairs: list[tuple[str, float]]) -> Path:
    ensure_dirs()
    apply_style()
    names = [p[0] for p in pairs][::-1]
    vals = [p[1] for p in pairs][::-1]
    fig, ax = plt.subplots(figsize=(7, 4))
    colors = [PALETTE[0] if v >= 0 else PALETTE[5] for v in vals]
    ax.barh(names, vals, color=colors)
    ax.set_title("Figure 20. SHAP mean |impact| (synthetic)")
    ax.set_xlabel("Impact")
    fig.tight_layout()
    path = FIGURES_DIR / "20_shap_bar.png"
    fig.savefig(path)
    plt.close(fig)
    return path
