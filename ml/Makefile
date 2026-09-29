.PHONY: setup data train notebooks reports app test all

setup:
	pwsh -File scripts/setup.ps1

data:
	.venv/Scripts/python -c "from fra_dss.data import load_raw_claims, validate_claims; from fra_dss.data.load import write_json; from fra_dss.config import METRICS_DIR; df=load_raw_claims(); write_json(METRICS_DIR/'data_profile.json', validate_claims(df))"

train:
	.venv/Scripts/python -m fra_dss.cli run-all --mode fast

train-full:
	.venv/Scripts/python -m fra_dss.cli run-all --mode full

notebooks:
	.venv/Scripts/python scripts/execute_notebooks.py --mode fast

reports:
	.venv/Scripts/python -c "from fra_dss.reporting.pdf_builder import build_all_p0_pdfs, build_remaining_p1_pdfs; build_all_p0_pdfs(); build_remaining_p1_pdfs()"

app:
	.venv/Scripts/streamlit run app/streamlit_app.py

test:
	.venv/Scripts/pytest -q tests

all: train notebooks reports test
