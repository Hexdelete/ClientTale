from flask import Blueprint, jsonify, request

from app.auth_utils import login_required
from app.pdf_parser import parse_intake_pdf

pdf_import_bp = Blueprint("pdf_import", __name__)

ALLOWED_EXTENSION = ".pdf"


@pdf_import_bp.post("/pdf")
@login_required
def import_pdf():
    if "file" not in request.files:
        return jsonify({"error": "no file uploaded"}), 400

    upload = request.files["file"]
    if not upload.filename or not upload.filename.lower().endswith(ALLOWED_EXTENSION):
        return jsonify({"error": "file must be a PDF"}), 400

    try:
        parsed = parse_intake_pdf(upload.stream)
    except Exception as exc:  # noqa: BLE001 - surface parse failures to the UI
        return jsonify({"error": f"could not parse PDF: {exc}"}), 422

    return jsonify(parsed)
