# Model card: FRA claim-outcome champion (Set A LightGBM)

## Model details

- **Task:** Multiclass status (Approved, Pending, Rejected)
- **Default shipped model:** LightGBM on feature Set A (filing-time)
- **Artifact:** `backend/models/claim_outcome.joblib`
- **Framework:** scikit-learn Pipeline / ColumnTransformer + LightGBM
- **Explainability:** SHAP TreeExplainer

## Intended use

Academic mini-project demo and officer-facing DSS prototyping inside FRA Atlas. Inputs are claim form fields available at filing time.

## Out of scope

- Real administrative decisions on FRA claims
- Use of `rejection_reason` as a status feature
- Treating Set B process features as causal filing-time signals

## Metrics

Numbers are stored in `ml/reports/metrics/` (especially `champion.json` and `benchmark_master.csv`). Do not hand-type values into reports. Compare against `baseline_existing.json` from the prior GroupShuffleSplit LightGBM.

## Training data

Synthetic `fra_synthetic_claims.csv` (125k rows). See `DATA_CARD.md`.

## Ethical considerations

- Fairness metrics are a monitoring exercise on synthetic groups.
- Automating rejections risks harm; low-confidence cases should go to human review.
- Explicit synthetic-data disclosure must appear in the app and every PDF.

## Limitations

- High scores may reflect generator rules rather than real adjudication.
- Real-world performance is unknown.
- Spatial and process-aware lifts (Sets B/C) are diagnostic, not licences to ship circular features.
