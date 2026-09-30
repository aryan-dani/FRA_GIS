"""MoTA state-level claim stock forecasting (T5 stretch, 5 time points)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, r2_score

from fra_dss.config import METRICS_DIR, REPO_ROOT, SEED, ensure_dirs
from fra_dss.data.load import write_json

# Period files under data/
PERIOD_FILES = [
    ("2019-05", "31MAY2019.csv"),
    ("2022-11", "30NOV2022.csv"),
    ("2023-10", "31OCT2023.csv"),
    ("2024-06", "30JUN2024.csv"),
]


FOCUS_STATES = {
    "Madhya Pradesh",
    "Odisha",
    "Telangana",
    "Tripura",
}


def _find_numeric_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    lower = {c.lower().replace(" ", "").replace("_", ""): c for c in df.columns}
    for cand in candidates:
        key = cand.lower().replace(" ", "").replace("_", "")
        if key in lower:
            return lower[key]
    # fuzzy contains
    for c in df.columns:
        cl = c.lower()
        for cand in candidates:
            if cand.lower() in cl:
                return c
    return None


def load_mota_panel() -> pd.DataFrame:
    """Load MoTA CSVs into a long panel. Schema varies by file; best-effort parse."""
    data_dir = REPO_ROOT / "data"
    rows = []
    for period, fname in PERIOD_FILES:
        path = data_dir / fname
        if not path.exists():
            continue
        df = pd.read_csv(path)
        # Try common MoTA column patterns
        state_col = _find_numeric_col(df, ["state", "statename", "states/uts", "states"])
        if state_col is None:
            # first object column
            obj = [c for c in df.columns if df[c].dtype == object]
            state_col = obj[0] if obj else df.columns[0]
        claims_col = _find_numeric_col(
            df,
            [
                "totalclaimsreceived",
                "claimsreceived",
                "totalclaims",
                "no.ofclaimsreceived",
                "received",
            ],
        )
        titles_col = _find_numeric_col(
            df,
            [
                "titlessdistributed",
                "titlesdistributed",
                "titles",
                "no.oftitlesdistributed",
                "distributed",
            ],
        )
        for _, r in df.iterrows():
            state = str(r[state_col]).strip()
            if not state or state.lower() in {"total", "nan", "india"}:
                continue
            # Keep all states; flag focus ones
            claims = pd.to_numeric(r[claims_col], errors="coerce") if claims_col else np.nan
            titles = pd.to_numeric(r[titles_col], errors="coerce") if titles_col else np.nan
            rows.append(
                {
                    "period": period,
                    "state": state,
                    "claims_received": float(claims) if pd.notna(claims) else None,
                    "titles_distributed": float(titles) if pd.notna(titles) else None,
                    "is_focus": any(f.lower() in state.lower() for f in FOCUS_STATES),
                }
            )
    return pd.DataFrame(rows)


def run_mota_forecast() -> dict[str, Any]:
    """
    With only ~4 periods, use a simple time-index regression vs last-value baseline.
    Caveat: five (or fewer) time points cannot support complex forecasting.
    """
    ensure_dirs()
    panel = load_mota_panel()
    if panel.empty:
        report = {
            "skipped": True,
            "reason": "Could not parse MoTA period CSVs into a panel.",
            "caveat": "Only a handful of official time points exist; treat any forecast as illustrative.",
        }
        write_json(METRICS_DIR / "mota_forecast.json", report)
        return report

    period_to_t = {p: i for i, (p, _) in enumerate(PERIOD_FILES)}
    panel = panel.dropna(subset=["claims_received"]).copy()
    panel["t"] = panel["period"].map(period_to_t)

    results = []
    for state, g in panel.groupby("state"):
        g = g.sort_values("t")
        if len(g) < 3:
            continue
        # Leave last period out
        train, test = g.iloc[:-1], g.iloc[-1:]
        X_tr = train[["t"]].to_numpy()
        y_tr = train["claims_received"].to_numpy()
        X_te = test[["t"]].to_numpy()
        y_te = test["claims_received"].to_numpy()

        baseline = float(train["claims_received"].iloc[-1])  # last value
        base_mae = float(abs(baseline - y_te[0]))

        lr = LinearRegression()
        lr.fit(X_tr, y_tr)
        pred = float(lr.predict(X_te)[0])
        lr_mae = float(abs(pred - y_te[0]))

        ridge = Ridge(alpha=1.0)
        ridge.fit(X_tr, y_tr)
        pred_r = float(ridge.predict(X_te)[0])
        ridge_mae = float(abs(pred_r - y_te[0]))

        results.append(
            {
                "state": state,
                "is_focus": bool(g["is_focus"].iloc[0]),
                "n_periods": int(len(g)),
                "y_true_last": float(y_te[0]),
                "baseline_last_value": baseline,
                "baseline_mae": base_mae,
                "linear_pred": pred,
                "linear_mae": lr_mae,
                "ridge_pred": pred_r,
                "ridge_mae": ridge_mae,
            }
        )

    focus = [r for r in results if r["is_focus"]]
    report = {
        "synthetic_claims_note": (
            "MoTA aggregates are official-ish CSV extracts, not the synthetic claim microdata."
        ),
        "caveat": (
            "Only four period files were available. With so few time points, "
            "forecasts are illustrative only and must not inform policy."
        ),
        "n_states_evaluated": len(results),
        "mean_baseline_mae": float(np.mean([r["baseline_mae"] for r in results])) if results else None,
        "mean_linear_mae": float(np.mean([r["linear_mae"] for r in results])) if results else None,
        "mean_ridge_mae": float(np.mean([r["ridge_mae"] for r in results])) if results else None,
        "focus_states": focus,
        "all_states_sample": results[:20],
        "panel_periods": sorted(panel["period"].unique().tolist()),
    }
    write_json(METRICS_DIR / "mota_forecast.json", report)
    panel.to_csv(METRICS_DIR / "mota_panel.csv", index=False)
    return report


if __name__ == "__main__":
    print(json.dumps(run_mota_forecast(), indent=2)[:2000])
