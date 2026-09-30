import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import uuid
import re
import io
from datetime import datetime, timezone

import firebase_admin
from firebase_admin import credentials, firestore

# --- Setup ---
load_dotenv()

app = Flask(__name__)

# Local CRA may land on 3000/3001 if a port is busy; allow common local origins.
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "https://fra-atlas-one.vercel.app",
    "https://fra-atlas.vercel.app",
]
CORS(
    app,
    resources={r"/api/*": {"origins": origins}},
    supports_credentials=False,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)

# --- Firebase Admin Setup ---
CLAIMS_COLLECTION = "FRA_Claims"


def _init_firebase():
    if firebase_admin._apps:
        return

    credentials_json = (os.environ.get("FIREBASE_CREDENTIALS_JSON") or "").strip()
    if credentials_json:
        import json

        # Render / dotenv sometimes wraps the value in quotes
        if (credentials_json.startswith("'") and credentials_json.endswith("'")) or (
            credentials_json.startswith('"') and credentials_json.endswith('"')
        ):
            credentials_json = credentials_json[1:-1]

        try:
            cert = json.loads(credentials_json)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "FIREBASE_CREDENTIALS_JSON is not valid JSON. "
                "Paste the full service-account file as a single line."
            ) from exc

        firebase_admin.initialize_app(credentials.Certificate(cert))
        return

    credentials_path = os.environ.get(
        "FIREBASE_CREDENTIALS_PATH",
        os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "firebase-service-account.json"),
    )
    if not os.path.isabs(credentials_path):
        credentials_path = os.path.join(os.path.dirname(__file__), credentials_path)

    if not os.path.exists(credentials_path):
        raise ValueError(
            "Firebase credentials missing. Set FIREBASE_CREDENTIALS_JSON "
            "(Render) or FIREBASE_CREDENTIALS_PATH to a service-account JSON file."
        )

    firebase_admin.initialize_app(credentials.Certificate(credentials_path))
    os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", credentials_path)


_init_firebase()
db = firestore.client()

# DSS (scheme rules + claim-outcome model) — imported lazily-safe
from dss import (  # noqa: E402
    ModelNotReady,
    dss_bundle_for_payload,
    get_metrics,
    get_synthetic_claim,
    list_synthetic_claims,
    load_priority,
    model_ready,
    predict_from_claim,
    sample_synthetic_claims,
    scheme_catalog,
)
from dss.model_service import predict_outcome  # noqa: E402


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "ok",
            "service": "fra-gis-api",
            "dss_model_ready": model_ready(),
        }
    ), 200

# Optional OCR deps — loaded lazily so the API can start without them
nlp = None
vision_client = None
vision = None
pytesseract = None
cv2 = None
convert_from_path = None


def _ensure_ocr_deps():
    """Load OCR/NER dependencies on first document-processing request."""
    global nlp, vision_client, vision, pytesseract, cv2, convert_from_path

    if nlp is not None:
        return

    import spacy
    from pdf2image import convert_from_path as _convert_from_path
    from google.cloud import vision as _vision
    import pytesseract as _pytesseract
    import cv2 as _cv2

    nlp = spacy.load("en_core_web_lg")
    convert_from_path = _convert_from_path
    vision = _vision
    pytesseract = _pytesseract
    cv2 = _cv2
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    vision_client = vision.ImageAnnotatorClient()


def _serialize_claim(doc_snapshot):
    data = doc_snapshot.to_dict() or {}
    created_at = data.get("created_at")
    if hasattr(created_at, "isoformat"):
        data["created_at"] = created_at.isoformat()
    elif hasattr(created_at, "timestamp"):
        data["created_at"] = datetime.fromtimestamp(
            created_at.timestamp(), tz=timezone.utc
        ).isoformat()
    return {"id": doc_snapshot.id, **data}


# --- OCR & NER Processing Function ---

def extract_entities_from_text(text):
    """Extracts structured data from raw text using spaCy NER."""
    doc = nlp(text)

    entities = {
        "persons": [ent.text for ent in doc.ents if ent.label_ == "PERSON"],
        "locations": [ent.text for ent in doc.ents if ent.label_ in ["GPE", "LOC"]],
        "dates": [ent.text for ent in doc.ents if ent.label_ == "DATE"],
        "organizations": [ent.text for ent in doc.ents if ent.label_ == "ORG"],
    }

    area_pattern = re.compile(
        r"(\d+(\.\d+)?)\s*(hectares|hectare|acres|acre)", re.IGNORECASE
    )
    areas = area_pattern.findall(text)
    entities["land_area"] = [" ".join(match) for match in areas]

    claimant_name = entities["persons"][0] if entities["persons"] else None

    generic_locations = {"india", "state", "district", "village"}
    meaningful_locations = [
        loc for loc in entities["locations"] if loc.lower() not in generic_locations
    ]

    village = meaningful_locations[0] if len(meaningful_locations) > 0 else None
    district = meaningful_locations[1] if len(meaningful_locations) > 1 else None

    return {
        "name": claimant_name,
        "village": village,
        "district": district,
        "raw_entities": entities,
    }


def _ocr_with_google_vision(file_path):
    """Performs OCR using Google Vision API."""
    print("Attempting OCR with Google Vision API...")
    text = ""
    if file_path.lower().endswith(".pdf"):
        images_from_path = convert_from_path(file_path)
        for image_pil in images_from_path:
            img_byte_arr = io.BytesIO()
            image_pil.save(img_byte_arr, format="PNG")
            image = vision.Image(content=img_byte_arr.getvalue())
            response = vision_client.annotate_image(
                {
                    "image": image,
                    "features": [{"type_": vision.Feature.Type.DOCUMENT_TEXT_DETECTION}],
                }
            )
            if response.error.message:
                raise Exception(f"Google Vision API Error: {response.error.message}")
            text += response.full_text_annotation.text + "\n"
    else:
        with io.open(file_path, "rb") as image_file:
            content = image_file.read()
        image = vision.Image(content=content)
        response = vision_client.annotate_image(
            {
                "image": image,
                "features": [{"type_": vision.Feature.Type.DOCUMENT_TEXT_DETECTION}],
            }
        )
        if response.error.message:
            raise Exception(f"Google Vision API Error: {response.error.message}")
        text = response.full_text_annotation.text
    return text


def _preprocess_for_tesseract(image):
    """Preprocesses an image for better Tesseract OCR results."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]


def _ocr_with_tesseract(file_path):
    """Performs OCR using Tesseract as a fallback."""
    print("Google Vision failed. Falling back to Tesseract OCR...")
    text = ""
    if file_path.lower().endswith(".pdf"):
        images = convert_from_path(file_path)
        for i, image in enumerate(images):
            temp_image_path = f"temp_tesseract_page_{i}.png"
            image.save(temp_image_path)
            cv_image = cv2.imread(temp_image_path)
            processed_image = _preprocess_for_tesseract(cv_image)
            text += pytesseract.image_to_string(processed_image) + "\n"
            os.remove(temp_image_path)
    else:
        cv_image = cv2.imread(file_path)
        processed_image = _preprocess_for_tesseract(cv_image)
        text = pytesseract.image_to_string(processed_image)
    return text


def digitize_fra_document(file_path):
    """
    Processes a file using Google Vision and falls back to Tesseract on error.
    """
    _ensure_ocr_deps()
    text = ""
    try:
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            text = _ocr_with_google_vision(file_path)
        else:
            raise Exception("Google credentials not found. Skipping to fallback.")
    except Exception as e:
        print(f"An error occurred with Google Vision: {e}")
        text = _ocr_with_tesseract(file_path)

    if not text.strip():
        return None

    extracted_data = extract_entities_from_text(text)
    extracted_data["raw_text"] = text
    return extracted_data


# --- API Endpoints ---

@app.route("/api/process-document", methods=["POST"])
def process_document():
    """
    Handles file upload and performs OCR/NER, returning the extracted data without saving.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "No selected file"}), 400

    allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg", ".tiff"}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        return jsonify(
            {"error": f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"}
        ), 400

    temp_file_path = ""
    try:
        upload_folder = "uploads"
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        temp_file_path = os.path.join(upload_folder, str(uuid.uuid4()) + file_ext)
        file.save(temp_file_path)

        extracted_data = digitize_fra_document(temp_file_path)

        if not extracted_data or not extracted_data.get("raw_text"):
            return jsonify({"error": "Failed to extract any text from the document."}), 500

        return jsonify(extracted_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@app.route("/api/claims", methods=["GET"])
def get_claims():
    """List claims from Firestore and/or synthetic FRA dataset.

    Query params:
      source=all|synthetic|firestore (default: all)
      limit=N (default 5000 for synthetic; use 0 or 'all' for full synthetic set)
      offset=N
      state, status, q — optional filters for synthetic rows
    """
    try:
        source = (request.args.get("source") or "all").strip().lower()
        state = request.args.get("state")
        status = request.args.get("status")
        q = request.args.get("q")
        offset = int(request.args.get("offset") or 0)
        limit_raw = request.args.get("limit")

        claims: list = []

        if source in ("all", "firestore"):
            try:
                docs = (
                    db.collection(CLAIMS_COLLECTION)
                    .order_by("created_at", direction=firestore.Query.DESCENDING)
                    .stream()
                )
                for doc in docs:
                    item = _serialize_claim(doc)
                    item["source"] = "firestore"
                    claims.append(item)
            except Exception as firestore_err:
                # Allow synthetic-only demo if Firestore is unavailable
                if source == "firestore":
                    return jsonify({"error": str(firestore_err)}), 500

        if source in ("all", "synthetic"):
            if limit_raw is None:
                syn_limit = 5000
            elif str(limit_raw).lower() in ("0", "all", "none"):
                syn_limit = None
            else:
                syn_limit = max(1, int(limit_raw))

            synthetic, _total = list_synthetic_claims(
                state=state,
                status=status,
                q=q,
                limit=syn_limit,
                offset=offset if source == "synthetic" else 0,
            )
            claims.extend(synthetic)

        return jsonify(claims), 200
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/claims", methods=["POST"])
def create_claim():
    """Creates a new claim from user-submitted data (manual or reviewed)."""
    try:
        claim_data = request.get_json()

        if not claim_data or not claim_data.get("name"):
            return jsonify({"error": "Claimant name is required."}), 400

        if claim_data.get("raw_text"):
            existing = (
                db.collection(CLAIMS_COLLECTION)
                .where("raw_text", "==", claim_data["raw_text"])
                .limit(1)
                .stream()
            )
            if any(True for _ in existing):
                return jsonify(
                    {"error": "This document has already been processed and saved."}
                ), 409

        data_to_insert = {
            "name": claim_data.get("name"),
            "village": claim_data.get("village"),
            "district": claim_data.get("district"),
            "state": claim_data.get("state"),
            "claim_type": claim_data.get("claim_type"),
            "status": claim_data.get("status"),
            "latitude": claim_data.get("latitude"),
            "longitude": claim_data.get("longitude"),
            "raw_text": claim_data.get("raw_text"),
            "entities": claim_data.get("entities"),
            "created_at": firestore.SERVER_TIMESTAMP,
        }
        data_to_insert = {k: v for k, v in data_to_insert.items() if v is not None}

        _unused, doc_ref = db.collection(CLAIMS_COLLECTION).add(data_to_insert)
        created = doc_ref.get()
        return jsonify(_serialize_claim(created)), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/claims/<claim_id>", methods=["GET"])
def get_claim_by_id(claim_id):
    """Fetches a claim by Firestore ID or synthetic claim_id."""
    try:
        doc = db.collection(CLAIMS_COLLECTION).document(claim_id).get()
        if doc.exists:
            item = _serialize_claim(doc)
            item["source"] = "firestore"
            return jsonify(item), 200

        synthetic = get_synthetic_claim(claim_id)
        if synthetic:
            return jsonify(synthetic), 200

        return jsonify({"error": "Claim not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/claims/<claim_id>/status", methods=["PUT"])
def update_claim_status(claim_id):
    """Updates the status of a specific FRA claim."""
    data = request.get_json()
    new_status = data.get("status") if data else None

    if not new_status:
        return jsonify({"error": "Status is required"}), 400

    # Synthetic claims are read-only in the demo dataset
    if get_synthetic_claim(claim_id):
        return jsonify(
            {
                "error": "Synthetic demo claims are read-only. Status updates apply to digitized Firestore claims only."
            }
        ), 400

    try:
        doc_ref = db.collection(CLAIMS_COLLECTION).document(claim_id)
        doc = doc_ref.get()
        if not doc.exists:
            return jsonify({"error": "Claim not found"}), 404

        doc_ref.update({"status": new_status})
        updated = doc_ref.get()
        return jsonify(_serialize_claim(updated)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- Decision Support System (DSS) ---


@app.route("/api/dss/schemes", methods=["GET", "POST"])
def dss_schemes():
    """Rule-based CSS scheme recommendations (optional feature payload)."""
    try:
        if request.method == "GET":
            return jsonify({"schemes": scheme_catalog()}), 200

        payload = request.get_json() or {}
        from dss.scheme_rules import recommend_schemes
        from ml.features import claim_to_feature_dict

        features = claim_to_feature_dict(payload)
        for key, value in payload.items():
            if value is not None and value != "":
                features[key] = value
        return jsonify({"schemes": recommend_schemes(features), "features": features}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/dss/predict", methods=["POST"])
def dss_predict():
    """AI claim-outcome prediction + SHAP + scheme layering."""
    try:
        payload = request.get_json() or {}
        claim_id = payload.get("claim_id") or payload.get("id")
        if claim_id:
            doc = db.collection(CLAIMS_COLLECTION).document(claim_id).get()
            if doc.exists:
                claim = _serialize_claim(doc)
            else:
                claim = get_synthetic_claim(claim_id)
                if not claim:
                    return jsonify({"error": "Claim not found"}), 404
            # Overlay any extra feature fields from the POST body
            merged = {**claim, **payload}
            result = predict_from_claim(merged)
            result["claim_id"] = claim_id
            return jsonify(result), 200

        return jsonify(dss_bundle_for_payload(payload)), 200
    except ModelNotReady as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/dss/priority", methods=["GET"])
def dss_priority():
    """District priority scores for focus-state intervention planning."""
    try:
        state = request.args.get("state")
        rows = load_priority(state=state)
        return jsonify({"state": state, "districts": rows, "count": len(rows)}), 200
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/dss/synthetic-claims", methods=["GET"])
def dss_synthetic_claims():
    """Sampled synthetic claims for WebGIS demo (not the full 125k rows)."""
    try:
        state = request.args.get("state")
        status = request.args.get("status")
        limit = request.args.get("limit", 200)
        claims = sample_synthetic_claims(state=state, limit=limit, status=status)
        return jsonify({"claims": claims, "count": len(claims), "state": state}), 200
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/dss/metrics", methods=["GET"])
def dss_metrics():
    """Training metrics for the claim-outcome model."""
    metrics = get_metrics()
    if metrics is None:
        return jsonify({"error": "Metrics not found. Train the model first."}), 503
    return jsonify(metrics), 200


@app.route("/api/dss/benchmark", methods=["GET"])
def dss_benchmark():
    """ML leaderboard JSON from ml/reports/metrics/benchmark_master.csv (additive)."""
    try:
        import csv
        from pathlib import Path

        path = Path(__file__).resolve().parents[1] / "ml" / "reports" / "metrics" / "benchmark_master.csv"
        if not path.exists():
            return jsonify({"error": "Benchmark not found. Run ml pipeline first.", "rows": []}), 503
        with path.open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        champ_path = path.parent / "champion.json"
        champion = None
        if champ_path.exists():
            import json

            champion = json.loads(champ_path.read_text(encoding="utf-8"))
        return jsonify(
            {
                "rows": rows,
                "champion": champion,
                "synthetic": True,
                "disclosure": "Synthetic data. Not for real claim decisions.",
            }
        ), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/dss/reasons", methods=["POST"])
def dss_reasons():
    """Top rejection reasons for a claim payload (additive; requires auxiliary model)."""
    try:
        from dss.aux_models import predict_rejection_reasons
        from ml.features import claim_to_feature_dict

        payload = request.get_json() or {}
        features = claim_to_feature_dict(payload)
        features.update({k: v for k, v in payload.items() if v is not None and v != ""})
        return jsonify(predict_rejection_reasons(features)), 200
    except FileNotFoundError as e:
        return jsonify({"error": str(e), "reasons": []}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/dss/what-if", methods=["POST"])
def dss_what_if():
    """Actionable-field what-if search (additive)."""
    try:
        from dss.what_if import search_what_if
        from ml.features import claim_to_feature_dict

        payload = request.get_json() or {}
        features = claim_to_feature_dict(payload)
        features.update({k: v for k, v in payload.items() if v is not None and v != ""})

        def _predict(c):
            return predict_outcome(c)

        changes = search_what_if(_predict, features, target_lift=0.03)
        return jsonify({"changes": changes, "synthetic": True}), 200
    except ModelNotReady as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/dss/eta", methods=["POST"])
def dss_eta():
    """ETA point estimate for a claim (additive; resolved-claims regressor)."""
    try:
        from dss.aux_models import predict_eta_days
        from ml.features import claim_to_feature_dict

        payload = request.get_json() or {}
        features = claim_to_feature_dict(payload)
        features.update({k: v for k, v in payload.items() if v is not None and v != ""})
        return jsonify(predict_eta_days(features)), 200
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/dss/triage", methods=["GET"])
def dss_triage():
    """Ranked pending claims for backlog triage (additive sample)."""
    try:
        state = request.args.get("state")
        limit = int(request.args.get("limit", 50))
        claims = sample_synthetic_claims(state=state, limit=max(limit * 3, 150), status="Pending")
        # Score with reject probability when model ready
        ranked = []
        for claim in claims[:limit]:
            try:
                pred = predict_from_claim(claim)
                reject_p = float(pred.get("probabilities", {}).get("Rejected", 0))
            except Exception:
                reject_p = 0.0
            days = float(claim.get("processing_days") or 180)
            score = 100 * (0.45 * reject_p + 0.35 * min(days / 730.0, 1.0) + 0.20 * min(days / 730.0, 1.0))
            ranked.append({**claim, "reject_prob": round(reject_p, 4), "triage_score": round(score, 2)})
        ranked.sort(key=lambda r: r["triage_score"], reverse=True)
        return jsonify({"claims": ranked[:limit], "count": len(ranked[:limit]), "synthetic": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)
