from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash

from app.models import Staff

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    staff = Staff.query.filter_by(username=username).first()
    if not staff or not check_password_hash(staff.password_hash, password):
        return jsonify({"error": "invalid username or password"}), 401

    session["staff_id"] = staff.id
    return jsonify(staff.to_dict())


@auth_bp.post("/logout")
def logout():
    session.clear()
    return jsonify({"status": "ok"})


@auth_bp.get("/me")
def me():
    staff_id = session.get("staff_id")
    if not staff_id:
        return jsonify({"error": "not authenticated"}), 401
    staff = Staff.query.get(staff_id)
    if not staff:
        session.clear()
        return jsonify({"error": "not authenticated"}), 401
    return jsonify(staff.to_dict())
