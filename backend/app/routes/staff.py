from flask import Blueprint, jsonify, request, session
from werkzeug.security import generate_password_hash

from app import db
from app.auth_utils import login_required
from app.models import Case, Staff

staff_bp = Blueprint("staff", __name__)


@staff_bp.get("")
def list_staff():
    role = request.args.get("role")
    query = Staff.query
    if role:
        query = query.filter_by(role=role)
    query = query.filter_by(active=True).order_by(Staff.last_name, Staff.first_name)
    return jsonify([s.to_dict() for s in query.all()])


@staff_bp.post("")
@login_required
def add_staff():
    data = request.get_json(silent=True) or {}
    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    role = data.get("role")
    email = (data.get("email") or "").strip() or None
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not first_name or not last_name:
        return jsonify({"error": "first_name and last_name are required"}), 400
    if role not in ("lawyer", "paralegal", "admin"):
        return jsonify({"error": "role must be 'lawyer', 'paralegal', or 'admin'"}), 400
    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400
    if len(password) < 8:
        return jsonify({"error": "password must be at least 8 characters"}), 400
    if Staff.query.filter_by(username=username).first():
        return jsonify({"error": "username already exists"}), 409

    staff = Staff(
        first_name=first_name,
        last_name=last_name,
        role=role,
        email=email,
        username=username,
        password_hash=generate_password_hash(password),
        active=True,
    )
    db.session.add(staff)
    db.session.commit()
    return jsonify(staff.to_dict()), 201


@staff_bp.put("/<int:staff_id>")
@login_required
def update_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    data = request.get_json(silent=True) or {}

    if "first_name" in data:
        first_name = (data.get("first_name") or "").strip()
        if not first_name:
            return jsonify({"error": "first_name is required"}), 400
        staff.first_name = first_name
    if "last_name" in data:
        last_name = (data.get("last_name") or "").strip()
        if not last_name:
            return jsonify({"error": "last_name is required"}), 400
        staff.last_name = last_name
    if "role" in data:
        role = data.get("role")
        if role not in ("lawyer", "paralegal", "admin"):
            return jsonify({"error": "role must be 'lawyer', 'paralegal', or 'admin'"}), 400
        staff.role = role
    if "email" in data:
        staff.email = (data.get("email") or "").strip() or None
    if "username" in data:
        new_username = (data.get("username") or "").strip()
        if not new_username:
            return jsonify({"error": "username is required"}), 400
        existing = Staff.query.filter_by(username=new_username).first()
        if existing and existing.id != staff.id:
            return jsonify({"error": "username already exists"}), 409
        staff.username = new_username
    if data.get("password"):
        password = data["password"]
        if len(password) < 8:
            return jsonify({"error": "password must be at least 8 characters"}), 400
        staff.password_hash = generate_password_hash(password)

    db.session.commit()
    return jsonify(staff.to_dict())


@staff_bp.delete("/<int:staff_id>")
@login_required
def delete_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)

    if staff.id == session.get("staff_id"):
        return jsonify({"error": "cannot delete your own login"}), 400
    if Staff.query.count() <= 1:
        return jsonify({"error": "cannot delete the only remaining staff member"}), 400

    in_use = Case.query.filter(
        (Case.primary_lawyer_id == staff_id)
        | (Case.secondary_lawyer_id == staff_id)
        | (Case.legal_assistant_id == staff_id)
    ).first()

    if in_use:
        staff.active = False
        db.session.commit()
        return jsonify({"status": "deactivated", "reason": "staff assigned to existing cases"})

    db.session.delete(staff)
    db.session.commit()
    return jsonify({"status": "deleted"})
