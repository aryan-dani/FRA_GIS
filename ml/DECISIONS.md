# Decisions log

Every judgment call for the FRA DSS ML mini project. Dates use ISO format.

## 2026-03-29: Branch and scope

- Work on `feat/ml-dss` only. Do not push to `main` from this effort.
- Heavy ML deps stay in `ml/requirements.txt`. Backend requirements stay light for Render.

## 2026-03-29: Shipped artifact is Set A LightGBM

- Even if stacking or voting wins the leaderboard, the Flask contract artifact is LightGBM on Set A.
- Reason: `shap.TreeExplainer`, Render RAM, and under-25 MB joblib size.
- Ensembles may be stored under `ml/artifacts/models/` for probability experiments.

## 2026-03-29: Champion selection rule (before final test)

- Primary: highest mean macro-F1 on S1 (grouped district CV) on feature Set A.
- Ties: lower log loss, then lower latency per 1,000 rows.
- Recorded in `configs/experiment.yaml`.

## 2026-03-29: Feature sets

- Set A: filing-time only (deployable early-risk).
- Set B: A plus `committee_level_reached` and `processing_days` (process-aware, partly circular).
- Set C: A plus lat/lon (spatial). Top models only if time allows.
- `rejection_reason` never enters status features (perfect leakage).

## 2026-03-29: Locked test

- Whole districts held out to about 20% of rows, stratified as well as allocation allows.
- Indices under `reports/metrics/splits/`. Never used for model selection.

## 2026-03-29: Slow models

- KNN, MLP, calibrated SGD, sklearn GradientBoosting train on a documented subsample (8k) in CV when the fold is larger.
- Recorded in metrics JSON via train timing fields.

## 2026-03-29: ETA

- Trained on Approved and Rejected only. Pending `processing_days` treated as potentially right-censored.

## 2026-03-29: Writing standard

- No em dashes in reports, notebooks, docs, or comments.
- Every numeric claim in PDFs is read from `reports/metrics/`.

## 2026-03-29: Preprocessor vs prepare_features

- Keep `ml.features.prepare_features` for backend inference mapping.
- Training pipelines use `fra_dss.preprocessing` ColumnTransformer on Set A columns so process fields are ignored even if present.

## 2026-03-29: sklearn 1.9 LogisticRegression API

- Removed deprecated `multi_class` and unused `n_jobs` kwargs so logistic baselines train on scikit-learn 1.5 to 1.9.

## 2026-03-29: Fast-mode champion is XGBoost on Set A

- Pre-declared rule selected `xgboost` by S1 macro-F1 on Set A in fast mode.
- Shipped backend artifact remains LightGBM for TreeExplainer and Render size (see earlier decision).


## 2026-03-29: Extended stats and stretch tasks

- Ran S2 (random stratified) and S4 (leave-one-state-out) on core Set A models in fast mode.
- S2 is slightly optimistic versus S1 (small positive optimism_vs_s1).
- S4 macro-F1 drops sharply (state shift), which is an expected hardness signal.
- Bootstrap CIs and McNemar written to extended_stats.json.
- Conformal split prediction sets at alpha=0.1 (coverage near 0.89 on synthetic holdout).
- MoTA T5 forecast uses four period CSVs only; last-value baseline often competitive. Illustrative only.
- Notebook HTML exports under reports/pdf/notebooks_html/.
- P1 PDFs 03, 05, 06, 08, 09 deepened to pull live metrics.
