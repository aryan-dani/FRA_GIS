# FRA-GIS Project Progress

This document tracks the progress of the Forest Rights Act (FRA) Digitization & GIS-DSS Prototype.

## Phase 1: Document Digitization (OCR & NER)

- **Status:** In Progress
- **Completed:**
  - [x] Basic document upload (PDF/image) and text extraction using Tesseract OCR.
  - [x] Scanned text is saved to the database.
- **In Progress:**
  - [ ] Implementing Named Entity Recognition (NER) with spaCy to extract structured data (claimant name, village, dates, land area).
  - [ ] Updating the database schema to store structured entities.
  - [ ] Refining the OCR process with image preprocessing for better accuracy.
- **To Do:**
  - [ ] Train a custom NER model if pre-trained models are insufficient for FRA-specific terms.

## Phase 2: GIS Mapping – Building the FRA Atlas

- **Status:** Completed
- **Completed:**
  - [x] Created an interactive map using Leaflet.js.
  - [x] Displaying claim locations from the database as markers.
  - [x] Implemented popups to show basic claim information.
  - [x] Enhanced map with darker markers and polygon areas.
  - [x] Added a dedicated "Claim Detail" page with a map view for a single claim.

## Phase 3: Asset Mapping (Satellite Imagery & Classification)

- **Status:** Not Started
- **To Do:**
  - [ ] Select a sample region in Google Earth Engine (GEE).
  - [ ] Fetch satellite imagery (Landsat/Sentinel).
  - [ ] Perform supervised classification to identify land use (forest, farm, water).
  - [ ] Export the classified layer and overlay it on the Leaflet map.

## Phase 4: Web-Based Interface (Frontend & Backend)

- **Status:** Completed
- **Completed:**
  - [x] Developed a multi-page frontend using React.
  - [x] Created a backend server using Flask.
  - [x] Implemented API endpoints for file uploads and data retrieval.
  - [x] Built a professional UI with navigation, a dashboard, and data tables.
  - [x] Added an analytics dashboard with charts.

## Phase 5: Decision Support System (Rule-Based + AI-Enhanced)

- **Status:** Completed (demo)
- **Completed:**
  - [x] LightGBM claim-outcome model trained on synthetic FRA claims (`ml/train_claim_outcome.py`).
  - [x] Rule-based CSS scheme eligibility (PM-KISAN, JJM, MGNREGA, DAJGUA) in `backend/dss/scheme_rules.py`.
  - [x] Flask DSS endpoints: `/api/dss/predict`, `/schemes`, `/priority`, `/synthetic-claims`, `/metrics`.
  - [x] DSS page (`/dss`) with district priority table + synthetic claim map + SHAP / schemes panel.
  - [x] Claim detail page DSS panel for outcome prediction and scheme layering.
- **Notes:**
  - Use repo-root `.venv` for training and local API (`pip install -r backend/requirements.txt`).
  - Satellite asset mapping remains Phase 3 / future scope.
