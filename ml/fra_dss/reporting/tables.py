"""Tables helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from fra_dss.config import TABLES_DIR, ensure_dirs


def write_markdown_table(df: pd.DataFrame, name: str) -> Path:
    ensure_dirs()
    path = TABLES_DIR / name
    try:
        text = df.to_markdown(index=False)
    except Exception:
        cols = list(df.columns)
        lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
        for _, row in df.iterrows():
            lines.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
        text = "\n".join(lines)
    path.write_text(text, encoding="utf-8")
    df.to_csv(TABLES_DIR / name.replace(".md", ".csv"), index=False)
    return path
