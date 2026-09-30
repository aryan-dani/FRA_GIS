# Data card: fra_synthetic_claims.csv

## Motivation

Synthetic FRA (Forest Rights Act) claim records for SIH12508 Decision Support System prototyping. Generated for demonstration and academic evaluation.

## Composition

- **Rows:** 125,000
- **Columns:** 18 (`claim_id`, `state`, `district`, `village`, `adjacent_forest_area`, `latitude`, `longitude`, `claim_type`, `applicant_type`, `land_area_ha`, `forest_density_class`, `year_filed`, `documentation_completeness`, `gram_sabha_resolution`, `processing_days`, `committee_level_reached`, `status`, `rejection_reason`)
- **Focus states:** Madhya Pradesh, Tripura, Odisha, Telangana
- **Target status:** Approved ~46%, Pending ~31%, Rejected ~23% (mild imbalance)

## Sensitive fields

- `rejection_reason` is non-null only for Rejected rows. Do not use it as a status predictor (leakage).
- `committee_level_reached` and `processing_days` are process-stage variables and partly circular with outcome.

## Missingness

- `village` and `adjacent_forest_area` have missing values. They are dropped from ML feature sets and retained for GIS only.

## Distribution notes

- `land_area_ha` is heavily skewed (median near 1.4 ha, max 500).
- `claim_type` is dominated by IFR.
- Temporal drift: approval share falls and pending share rises after 2019.
- Strong state effects (for example Tripura versus Telangana pending rates).

## Collection process

Synthetic generator (not field-collected MoTA case files). Separate MoTA aggregate CSVs and fringe-village files exist under `data/` for context and stretch forecasting.

## Recommended splits

- Group by `district` for generalization.
- Temporal and leave-one-state-out for shift stress tests.
- Lock a district-held-out final test before experimentation.

## Ethical note

This card describes synthetic data. Models trained here must not decide real FRA claims.
