"""Statistical tests for model comparison."""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import stats


def friedman_nemenyi(score_matrix: np.ndarray, model_names: list[str]) -> dict[str, Any]:
    """score_matrix shape (n_folds, n_models). Higher is better."""
    if score_matrix.shape[1] < 3 or score_matrix.shape[0] < 3:
        return {"skipped": True, "reason": "need >=3 models and >=3 folds"}
    stat, p = stats.friedmanchisquare(*[score_matrix[:, i] for i in range(score_matrix.shape[1])])
    result: dict[str, Any] = {
        "friedman_stat": float(stat),
        "friedman_p": float(p),
        "models": model_names,
    }
    try:
        import scikit_posthocs as sp
        import pandas as pd

        # posthoc expects (n_obs, n_models) with model columns
        df = pd.DataFrame(score_matrix, columns=model_names)
        ph = sp.posthoc_nemenyi_friedman(df.to_numpy())
        ph.index = model_names
        ph.columns = model_names
        result["nemenyi_pvalues"] = ph.round(4).to_dict()
    except Exception as exc:
        result["nemenyi_error"] = str(exc)
    return result


def paired_wilcoxon(a: np.ndarray, b: np.ndarray) -> dict[str, float]:
    if len(a) < 5:
        return {"statistic": float("nan"), "pvalue": float("nan")}
    stat, p = stats.wilcoxon(a, b)
    return {"statistic": float(stat), "pvalue": float(p)}


def mcnemar_from_preds(y_true: np.ndarray, pred_a: np.ndarray, pred_b: np.ndarray) -> dict[str, float]:
    a_correct = pred_a == y_true
    b_correct = pred_b == y_true
    n01 = int(np.sum(~a_correct & b_correct))
    n10 = int(np.sum(a_correct & ~b_correct))
    # continuity-corrected McNemar
    if n01 + n10 == 0:
        return {"statistic": 0.0, "pvalue": 1.0}
    stat = (abs(n01 - n10) - 1) ** 2 / (n01 + n10)
    p = float(stats.chi2.sf(stat, df=1))
    return {"statistic": float(stat), "pvalue": p, "n01": n01, "n10": n10}


def bootstrap_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    metric_fn,
    n_boot: int = 1000,
    seed: int = 42,
) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    vals = []
    n = len(y_true)
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        vals.append(float(metric_fn(y_true[idx], y_pred[idx])))
    arr = np.asarray(vals)
    return {
        "mean": float(arr.mean()),
        "ci_low": float(np.percentile(arr, 2.5)),
        "ci_high": float(np.percentile(arr, 97.5)),
    }
