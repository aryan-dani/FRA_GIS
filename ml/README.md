# FRA DSS ML package

Synthetic FRA claims Decision Support System for the SIH12508 mini project.

**Disclosure:** the training data is synthetic. Scores may reflect generator rules. Real-world performance is unknown. Do not use this model for real claim decisions.

## Setup (Windows)

```powershell
cd ml
.\scripts\setup.ps1
.\.venv\Scripts\Activate.ps1
```

## Setup (Linux / macOS)

```bash
cd ml
bash scripts/setup.sh
source .venv/bin/activate
```

## One-command run

```powershell
# Fast smoke (about 30k rows)
.\scripts\run_all.ps1 -Mode fast

# Full 125k (longer)
.\scripts\run_all.ps1 -Mode full
```

```bash
bash scripts/run_all.sh fast
```

Or:

```bash
python -m fra_dss.cli run-all --mode fast
```

## Notebooks

```powershell
python scripts/execute_notebooks.py
python scripts/execute_notebooks.py --execute
jupyter lab notebooks
```

Kernel name: `fra-dss`.

## Streamlit demo

```powershell
streamlit run app/streamlit_app.py
```

## Folder map

| Path | Purpose |
|------|---------|
| `fra_dss/` | Installable package |
| `configs/` | Experiment, DSS weights, remediation |
| `reports/metrics/` | All numbers for PDFs and notebooks |
| `reports/figures/` | PNG / HTML figures |
| `reports/pdf/` | Generated PDFs |
| `artifacts/models/` | Champion and auxiliary models |
| `notebooks/` | Executed story notebooks |
| `app/` | Standalone Streamlit DSS |
| `tests/` | pytest |

## Reading results

1. `reports/metrics/benchmark_master.csv` leaderboard
2. `reports/metrics/champion.json` pre-declared selection rule winner
3. `reports/metrics/leakage_audit.json` leakage findings
4. `reports/pdf/07_Executive_Summary.pdf` two-page summary

## Backend artifact

`python ml/train_claim_outcome.py --legacy-only` writes `backend/models/claim_outcome.joblib` with the existing Flask contract (Set A LightGBM).

## Troubleshooting

- **ImportError fra_dss:** run `pip install -e ml` from `ml/` with the venv active.
- **SHAP missing on Render:** backend already lists shap; local ML venv also installs it.
- **Vercel ESLint:** keep frontend hooks deps clean; `CI=true npm run build`.
- **Slow full mode:** use `--mode fast` for iteration; caches live in `artifacts/cache/` (gitignored).
