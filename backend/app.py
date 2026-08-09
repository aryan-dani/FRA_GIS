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

origins = [
    "http://localhost:3000",
    "https://fra-atlas-one.vercel.app",
    "https://fra-atlas.vercel.app",
]
CORS(app, resources={r"/api/*": {"origins": origins}})

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


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "fra-gis-api"}), 200

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
    """Fetches all FRA claims from Firestore."""
    try:
        docs = (
            db.collection(CLAIMS_COLLECTION)
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .stream()
        )
        return jsonify([_serialize_claim(doc) for doc in docs]), 200
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
    """Fetches a single FRA claim by its Firestore document ID."""
    try:
        doc = db.collection(CLAIMS_COLLECTION).document(claim_id).get()
        if doc.exists:
            return jsonify(_serialize_claim(doc)), 200
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


if __name__ == "__main__":
    app.run(debug=True, port=5001)
