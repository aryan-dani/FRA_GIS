"""Plot style: colorblind-safe palette."""

from __future__ import annotations

import matplotlib.pyplot as plt

# Okabe-Ito colorblind-safe palette
PALETTE = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00", "#F0E442", "#000000"]


def apply_style() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 120,
            "savefig.dpi": 300,
            "font.size": 11,
            "axes.titlesize": 13,
            "axes.labelsize": 11,
            "axes.prop_cycle": plt.cycler(color=PALETTE),
        }
    )
