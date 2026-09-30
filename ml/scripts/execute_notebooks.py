"""Generate and optionally execute notebooks."""

from __future__ import annotations

import argparse
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

ML_ROOT = Path(__file__).resolve().parents[1]
NB_DIR = ML_ROOT / "notebooks"

NOTEBOOKS = [
    ("00_project_overview.ipynb", "Project overview and synthetic-data disclosure"),
    ("01_eda.ipynb", "Exploratory data analysis"),
    ("02_preprocessing_pipeline.ipynb", "Preprocessing pipeline comparisons"),
    ("03_baselines.ipynb", "Baseline classifiers"),
    ("04_bagging_models.ipynb", "Bagging family"),
    ("05_boosting_models.ipynb", "Boosting family"),
    ("06_stacking_voting_blending.ipynb", "Ensembles"),
    ("07_hyperparameter_tuning.ipynb", "Optuna / grid search"),
    ("08_evaluation_and_benchmark.ipynb", "Master benchmark"),
    ("09_explainability_calibration_fairness.ipynb", "Explainability and fairness"),
    ("10_auxiliary_tasks_reasons_eta_segmentation.ipynb", "Auxiliary ML tasks"),
    ("11_dss_engine_demo.ipynb", "DSS engine demo"),
]


def make_nb(title: str, mode: str = "fast") -> nbformat.NotebookNode:
    nb = new_notebook()
    nb.cells = [
        new_markdown_cell(
            f"# {title}\n\n"
            f"**Objective.** Demonstrate the FRA DSS ML step for: {title}.\n\n"
            f"**Inputs.** `data/fra_synthetic_claims.csv` (synthetic).\n\n"
            f"**Outputs.** Figures under `ml/reports/figures/` and metrics JSON.\n\n"
            f"**Runtime.** Fast mode target under 10 minutes.\n\n"
            "Disclosure: synthetic data. Real-world performance is unknown."
        ),
        new_code_cell(
            "MODE = 'fast'\n"
            "from pathlib import Path\n"
            "import sys\n"
            "ML_ROOT = Path('..').resolve() if Path('fra_dss').exists() is False else Path('.').resolve()\n"
            "# notebooks run with cwd = ml/notebooks\n"
            "sys.path.insert(0, str(Path.cwd().parent))\n"
            "from fra_dss.config import ensure_dirs, METRICS_DIR, FIGURES_DIR\n"
            "from fra_dss.data import load_claims, validate_claims, audit_leakage\n"
            "from fra_dss.data.load import load_raw_claims, write_json, provenance\n"
            "ensure_dirs()\n"
            "print('MODE', MODE)"
        ),
        new_code_cell(
            "df = load_claims(mode=MODE)\n"
            "print(df.shape)\n"
            "df['status'].value_counts()"
        ),
        new_markdown_cell(
            "### Story\n"
            "Notice class balance and state effects. Pending share rises in later years."
        ),
        new_code_cell(
            "from fra_dss.viz.eda import save_target_balance, save_temporal_drift, save_status_by_state\n"
            "save_target_balance(df)\n"
            "save_status_by_state(df)\n"
            "save_temporal_drift(df)\n"
            "print('figures written to', FIGURES_DIR)"
        ),
        new_markdown_cell("## Key takeaways\nResults are written to metrics files. Do not hand-type numbers into reports."),
    ]
    # Specialize a few notebooks
    if "benchmark" in title.lower() or "08" in title:
        nb.cells.append(
            new_code_cell(
                "import pandas as pd\n"
                "path = METRICS_DIR / 'benchmark_master.csv'\n"
                "print(path.exists())\n"
                "if path.exists():\n"
                "    display(pd.read_csv(path).sort_values('s1_macro_f1_mean', ascending=False).head(15))"
            )
        )
    if "dss" in title.lower():
        nb.cells.append(
            new_code_cell(
                "from fra_dss.dss import recommend\n"
                "claim = df.iloc[0].to_dict()\n"
                "try:\n"
                "    rec = recommend(claim)\n"
                "    print(rec.predicted_status, rec.probabilities)\n"
                "except Exception as e:\n"
                "    print('DSS needs trained artifact:', e)"
            )
        )
    return nb


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="fast")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    NB_DIR.mkdir(parents=True, exist_ok=True)
    for fname, title in NOTEBOOKS:
        nb = make_nb(title, args.mode)
        path = NB_DIR / fname
        nbformat.write(nb, path)
        print("wrote", path)
        if args.execute:
            try:
                import nbclient

                client = nbclient.NotebookClient(nb, timeout=600, kernel_name="python3")
                client.execute()
                nbformat.write(nb, path)
                print("executed", path)
            except Exception as exc:
                print("execute failed", path, exc)


if __name__ == "__main__":
    main()
