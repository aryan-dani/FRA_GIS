# FRA Atlas — WebGIS Decision Support System

Prototype platform for digitizing, mapping, and monitoring **Forest Rights Act (FRA)** claims — built for Smart India Hackathon 2025 (**SIH12508**, Ministry of Tribal Affairs).

**Live app:** [https://fra-atlas-one.vercel.app](https://fra-atlas-one.vercel.app)  
**API:** [https://fra-gis.onrender.com](https://fra-gis.onrender.com)  
**Problem statement:** [PROBLEM_STATEMENT.md](PROBLEM_STATEMENT.md)

---

## Overview

FRA Atlas helps agencies move from paper-heavy FRA workflows to a structured digital pipeline:

1. Capture claim data (manual entry or OCR-assisted digitization)
2. Store and manage records in Firestore
3. Visualize claims on a WebGIS map
4. Analyze trends and official state-level MoTA statistics

Focus states for the SIH brief: **Madhya Pradesh**, **Tripura**, **Odisha**, and **Telangana**.

---

## Features

| Area | What it does |
| --- | --- |
| **Dashboard** | Claim KPIs and Google Maps view of claim locations |
| **Claims ledger** | Search, filter, status updates, CSV export |
| **Claim detail** | Full record view with map and extracted text |
| **Analytics** | Charts for status, type, and regional patterns |
| **FRA Stats** | Official MoTA state-wise statistics (multi-period Excel → JSON) |
| **OCR pipeline** | Document upload via Flask → Vision / Tesseract fallback |

---

## Architecture

```text
┌─────────────────────┐         ┌──────────────────────┐
│  React SPA (Vercel) │────────▶│  Flask API (Render)  │
│  Dashboard / GIS    │         │  OCR + claims API    │
└─────────┬───────────┘         └──────────┬───────────┘
          │                                │
          │         Firestore              │
          └─────────────(claims)───────────┘
```

- **Frontend** talks to the Render API for live claims CRUD and OCR.
- **Firestore** stores claim documents (`FRA_Claims`).
- **Static MoTA stats** ship as JSON in the frontend (converted from Excel).

---

## Tech stack

| Layer | Stack |
| --- | --- |
| Frontend | React 19, React Bootstrap, React Router, Chart.js, Google Maps |
| Backend | Python, Flask, Gunicorn, Firebase Admin |
| Database | Firebase Firestore (Spark) |
| OCR | Google Cloud Vision (primary), Tesseract (fallback) |
| Deploy | Frontend → Vercel · Backend → Render |

---

## Repository layout

```text
FRA_GIS/
├── frontend/                 # CRA React app
│   ├── src/data/             # FRA statistics JSON
│   └── ...
├── backend/                  # Flask API
├── data/                     # Source Excel (MoTA FRA statistics)
├── scripts/                  # Data conversion utilities
├── PROBLEM_STATEMENT.md      # SIH12508 brief
└── README.md
```

---

## Quick start

### Prerequisites

- Node.js 18+ and npm  
- Python 3.11+  
- Firebase project with Firestore enabled  

### 1. Clone

```bash
git clone https://github.com/aryan-dani/FRA-GIS.git
cd FRA-GIS
```

### 2. Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
# equivalent: npm start
```

Set in `frontend/.env`:

```env
REACT_APP_API_URL=http://localhost:5001
REACT_APP_GOOGLE_MAPS_API_KEY=your_maps_javascript_api_key
# Optional Firebase web config if used by other modules
REACT_APP_FIREBASE_API_KEY=
REACT_APP_FIREBASE_AUTH_DOMAIN=
REACT_APP_FIREBASE_PROJECT_ID=
REACT_APP_FIREBASE_STORAGE_BUCKET=
REACT_APP_FIREBASE_MESSAGING_SENDER_ID=
REACT_APP_FIREBASE_APP_ID=
```

Enable **Maps JavaScript API** for that key in Google Cloud Console. Restart `npm run dev` after changing env.

App: [http://localhost:3000](http://localhost:3000)

### 3. Backend

Use the project virtualenv at the repo root:

```bash
# from repo root (first time)
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS / Linux
# source .venv/bin/activate

cd backend
cp .env.example .env
pip install -r requirements.txt
```

**One-command local demo (Windows):** from the repo root run:

```powershell
.\start-dev.ps1
```

This opens Flask (`:5001`) and the React app (`npm run dev` on `:3000`) in two terminals.

Place a service-account file at `backend/firebase-service-account.json`, or set:

```env
FIREBASE_CREDENTIALS_PATH=firebase-service-account.json
# Render: FIREBASE_CREDENTIALS_JSON=<one-line JSON>
```

```bash
python app.py
```

API: [http://localhost:5001](http://localhost:5001)  
Health check: `GET /api/health`

---

## Key API routes

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Liveness |
| `GET` | `/api/claims` | List claims |
| `POST` | `/api/claims` | Create claim |
| `GET` | `/api/claims/<id>` | Claim by ID |
| `PUT` | `/api/claims/<id>/status` | Update status |
| `POST` | `/api/process-document` | OCR upload |
| `POST` | `/api/dss/predict` | Claim-outcome ML + SHAP + CSS schemes |
| `GET`/`POST` | `/api/dss/schemes` | Scheme catalog / rule-based recommendations |
| `GET` | `/api/dss/priority` | District priority scores (`?state=`) |
| `GET` | `/api/dss/synthetic-claims` | Sampled synthetic claims for map demo |
| `GET` | `/api/dss/metrics` | Training metrics for the outcome model |
| `GET` | `/api/dss/benchmark` | ML leaderboard JSON (additive) |
| `POST` | `/api/dss/reasons` | Top rejection reasons (additive) |
| `POST` | `/api/dss/what-if` | Actionable-field what-if (additive) |
| `POST` | `/api/dss/eta` | ETA days point estimate (additive) |
| `GET` | `/api/dss/triage` | Ranked pending backlog sample (additive) |

---

## ML + Decision Support System

### Mini project package (`ml/`)

Full leakage-safe zoo, notebooks, PDFs, and Streamlit demo live under [`ml/`](ml/). See [`ml/README.md`](ml/README.md).

```powershell
cd ml
.\scripts\setup.ps1
.\scripts\run_all.ps1 -Mode fast
streamlit run app/streamlit_app.py
```

**Disclosure:** training uses synthetic claims. Real-world performance is unknown. Do not use for real claim decisions.

### Backend artifact (Flask contract)

```bash
.\ml\.venv\Scripts\Activate.ps1
python ml/train_claim_outcome.py --legacy-only
```

Artifacts written to [`backend/models/`](backend/models/):

- `claim_outcome.joblib` — preprocessor + LightGBM (Set A / contract columns)
- `metrics.json` — holdout accuracy / macro-F1 / per-class recall
- `priority_by_district.json` — district priority table for the DSS UI

UI route: `/dss` — focus-state priority table, synthetic claim map, SHAP drivers, CSS schemes, ML benchmark table, and what-if panel. Claim detail pages also show a DSS panel.

Synthetic claims CSV lives at [`backend/data/fra_synthetic_claims.csv`](backend/data/fra_synthetic_claims.csv) (and `data/`). `GET /api/claims?source=all` merges Firestore + synthetic rows (default `limit=5000`; use `limit=all` for the full 125k).

---

## FRA statistics data

Official MoTA workbook lives at [`data/Statistics_FRA_Claims.xlsx`](data/Statistics_FRA_Claims.xlsx).

Regenerate frontend JSON after updating the Excel:

```bash
python scripts/convert_fra_stats.py
```

Output: [`frontend/src/data/fraClaimsStatistics.json`](frontend/src/data/fraClaimsStatistics.json)  
UI route: `/#/fra-statistics`

Periods included: June 2024, October 2023, November 2022, May 2019.

---

## Deployment

| Service | URL / notes |
| --- | --- |
| Frontend (Vercel) | Project root directory: `frontend` · Production branch: `main` |
| Backend (Render) | Root: `backend` · Start: `gunicorn app:app --bind 0.0.0.0:$PORT` |
| Env on Vercel | `REACT_APP_API_URL=https://fra-gis.onrender.com` (+ Firebase keys if needed) |
| Env on Render | `FIREBASE_CREDENTIALS_JSON` (service account as one line) |

Free-tier Render instances sleep when idle; first API request after idle can take ~30–60s.

---

## Roadmap

Tracked in [`PROGRESS.md`](PROGRESS.md). High-level status:

- OCR / NER pipeline — in progress  
- WebGIS atlas & web UI — done  
- MoTA FRA statistics tab — done  
- Claim-outcome ML + CSS scheme DSS — done (demo rules + LightGBM)  
- Satellite asset mapping (GEE) — not started  

---

## Team

Built by **Team Evonex** for SIH 2025.

- Aryan Dani — [LinkedIn](https://www.linkedin.com/in/aryan-dani/)  
- Repository — [github.com/aryan-dani/FRA-GIS](https://github.com/aryan-dani/FRA-GIS)

---

## License

MIT — see [LICENSE](LICENSE).
