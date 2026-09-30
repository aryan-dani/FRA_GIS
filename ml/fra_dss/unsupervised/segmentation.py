"""Unsupervised district segmentation and anomaly flags."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.metrics import davies_bouldin_score, silhouette_score
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

from fra_dss.config import SEED


def district_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (state, district), g in df.groupby(["state", "district"]):
        rows.append(
            {
                "state": state,
                "district": district,
                "n": len(g),
                "reject_rate": float((g["status"] == "Rejected").mean()),
                "pending_rate": float((g["status"] == "Pending").mean()),
                "mean_days": float(pd.to_numeric(g["processing_days"], errors="coerce").mean()),
                "mean_land": float(pd.to_numeric(g["land_area_ha"], errors="coerce").mean()),
            }
        )
    return pd.DataFrame(rows)


def segment_districts(df: pd.DataFrame, k: int = 4) -> dict[str, Any]:
    agg = district_aggregates(df)
    feats = ["reject_rate", "pending_rate", "mean_days", "mean_land"]
    X = StandardScaler().fit_transform(agg[feats].fillna(0))
    results = {}
    for name, model in {
        "kmeans": KMeans(n_clusters=k, random_state=SEED, n_init=10),
        "gmm": GaussianMixture(n_components=k, random_state=SEED),
        "agglo": AgglomerativeClustering(n_clusters=k),
    }.items():
        labels = model.fit_predict(X) if name != "gmm" else model.fit(X).predict(X)
        sil = float(silhouette_score(X, labels)) if len(set(labels)) > 1 else float("nan")
        db = float(davies_bouldin_score(X, labels)) if len(set(labels)) > 1 else float("nan")
        results[name] = {"silhouette": sil, "davies_bouldin": db, "labels": labels.tolist()}
    pca = PCA(n_components=2, random_state=SEED).fit_transform(X)
    agg["pc1"] = pca[:, 0]
    agg["pc2"] = pca[:, 1]
    agg["segment_kmeans"] = results["kmeans"]["labels"]
    return {"metrics": {k: {"silhouette": v["silhouette"], "davies_bouldin": v["davies_bouldin"]} for k, v in results.items()}, "frame": agg}


def claim_anomalies(df: pd.DataFrame) -> dict[str, Any]:
    land = pd.to_numeric(df["land_area_ha"], errors="coerce").fillna(1.0).to_numpy().reshape(-1, 1)
    iso = IsolationForest(random_state=SEED, contamination=0.02)
    flags = iso.fit_predict(land)
    n_flag = int((flags == -1).sum())
    return {
        "n_flagged": n_flag,
        "rate": float(n_flag / len(df)),
        "rule": "IsolationForest on land_area_ha (demo)",
    }
