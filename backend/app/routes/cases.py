import re
from datetime import date, datetime

from flask import Blueprint, Response, jsonify, request
from sqlalchemy import or_
from sqlalchemy.orm import aliased

from app import db
from app.auth_utils import login_required
from app.models import Case, CaseEvent, OpposingCounsel, Staff

cases_bp = Blueprint("cases", __name__)

DATE_FIELDS = [
    "date_of_event",
    "sol_date",
    "conf_int_check_date",
    "dob",
    "dod",
]

STRING_FIELDS = [
    "status",
    "case_type",
    "county",
    "judge",
    "injured_first_name",
    "injured_last_name",
    "ssn",
    "height",
    "weight",
    "client_first_name",
    "client_last_name",
    "address_line1",
    "address_line2",
    "city",
    "state",
    "zip",
    "country",
    "work_phone",
    "email",
    "case_synopsis",
    "intake_comments",
]

INT_FIELDS = ["age"]

FK_FIELDS = ["primary_lawyer_id", "secondary_lawyer_id", "legal_assistant_id"]


def _parse_date(value):
    if not value:
        return None
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


def _parse_time(value):
    if not value:
        return None
    return datetime.strptime(value, "%H:%M").time()


def _apply_fields(case, data):
    for field in STRING_FIELDS:
        if field in data:
            setattr(case, field, data[field] or None)
    for field in DATE_FIELDS:
        if field in data:
            setattr(case, field, _parse_date(data[field]))
    for field in INT_FIELDS:
        if field in data:
            val = data[field]
            setattr(case, field, int(val) if val not in (None, "") else None)
    for field in FK_FIELDS:
        if field in data:
            val = data[field]
            setattr(case, field, int(val) if val not in (None, "") else None)


@cases_bp.get("")
@login_required
def list_cases():
    search = (request.args.get("search") or "").strip()
    query = Case.query
    if search:
        like = f"%{search}%"
        primary = aliased(Staff)
        secondary = aliased(Staff)
        assistant = aliased(Staff)
        query = (
            query.outerjoin(primary, Case.primary_lawyer_id == primary.id)
            .outerjoin(secondary, Case.secondary_lawyer_id == secondary.id)
            .outerjoin(assistant, Case.legal_assistant_id == assistant.id)
            .filter(
                or_(
                    Case.case_number.ilike(like),
                    Case.status.ilike(like),
                    Case.county.ilike(like),
                    Case.client_first_name.ilike(like),
                    Case.client_last_name.ilike(like),
                    Case.injured_first_name.ilike(like),
                    Case.injured_last_name.ilike(like),
                    primary.first_name.ilike(like),
                    primary.last_name.ilike(like),
                    secondary.first_name.ilike(like),
                    secondary.last_name.ilike(like),
                    assistant.first_name.ilike(like),
                    assistant.last_name.ilike(like),
                )
            )
        )
    query = query.order_by(Case.updated_at.desc())

    today = date.today()
    results = []
    for case in query.all():
        payload = case.to_dict()
        upcoming = [e.to_dict() for e in case.events if e.event_date and e.event_date >= today]
        payload["upcoming_events"] = upcoming
        results.append(payload)
    return jsonify(results)


@cases_bp.get("/<int:case_id>")
@login_required
def get_case(case_id):
    case = Case.query.get_or_404(case_id)
    return jsonify(case.to_dict(include_events=True))


@cases_bp.post("")
@login_required
def create_case():
    data = request.get_json(silent=True) or {}
    case_number = (data.get("case_number") or "").strip()
    if not case_number:
        return jsonify({"error": "case_number is required"}), 400
    if Case.query.filter_by(case_number=case_number).first():
        return jsonify({"error": "case_number already exists"}), 409

    for fk_field, role in (
        ("primary_lawyer_id", "lawyer"),
        ("secondary_lawyer_id", "lawyer"),
        ("legal_assistant_id", "paralegal"),
    ):
        val = data.get(fk_field)
        if val and not Staff.query.get(int(val)):
            return jsonify({"error": f"{fk_field} does not reference a valid staff member"}), 400

    case = Case(case_number=case_number, status=data.get("status") or "Pending")
    _apply_fields(case, data)
    db.session.add(case)
    db.session.commit()
    return jsonify(case.to_dict()), 201


@cases_bp.put("/<int:case_id>")
@login_required
def update_case(case_id):
    case = Case.query.get_or_404(case_id)
    data = request.get_json(silent=True) or {}

    new_case_number = (data.get("case_number") or "").strip()
    if new_case_number and new_case_number != case.case_number:
        if Case.query.filter_by(case_number=new_case_number).first():
            return jsonify({"error": "case_number already exists"}), 409
        case.case_number = new_case_number

    _apply_fields(case, data)
    db.session.commit()
    return jsonify(case.to_dict())


@cases_bp.delete("/<int:case_id>")
@login_required
def delete_case(case_id):
    case = Case.query.get_or_404(case_id)
    db.session.delete(case)
    db.session.commit()
    return jsonify({"status": "deleted"})


@cases_bp.post("/<int:case_id>/events")
@login_required
def add_event(case_id):
    case = Case.query.get_or_404(case_id)
    data = request.get_json(silent=True) or {}
    event_type = (data.get("event_type") or "").strip()
    event_date = data.get("event_date")
    if not event_type or not event_date:
        return jsonify({"error": "event_type and event_date are required"}), 400

    event = CaseEvent(
        case_id=case.id,
        event_type=event_type,
        event_date=_parse_date(event_date),
        event_time=_parse_time(data.get("event_time")),
        description=data.get("description") or None,
    )
    db.session.add(event)
    db.session.commit()
    return jsonify(event.to_dict()), 201


@cases_bp.put("/<int:case_id>/events/<int:event_id>")
@login_required
def update_event(case_id, event_id):
    event = CaseEvent.query.filter_by(id=event_id, case_id=case_id).first_or_404()
    data = request.get_json(silent=True) or {}
    if "event_type" in data:
        event.event_type = data["event_type"]
    if "event_date" in data:
        event.event_date = _parse_date(data["event_date"])
    if "event_time" in data:
        event.event_time = _parse_time(data["event_time"])
    if "description" in data:
        event.description = data["description"] or None
    db.session.commit()
    return jsonify(event.to_dict())


@cases_bp.delete("/<int:case_id>/events/<int:event_id>")
@login_required
def delete_event(case_id, event_id):
    event = CaseEvent.query.filter_by(id=event_id, case_id=case_id).first_or_404()
    db.session.delete(event)
    db.session.commit()
    return jsonify({"status": "deleted"})


def _ics_escape(value):
    return (value or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


@cases_bp.get("/<int:case_id>/events/export.ics")
@login_required
def export_case_events_ics(case_id):
    case = Case.query.get_or_404(case_id)
    today = date.today()
    upcoming = [e for e in case.events if e.event_date and e.event_date >= today]

    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//ClientTale//Case Events//EN"]
    for event in upcoming:
        summary = f"{event.event_type} — Case #{case.case_number}"
        if event.event_time:
            dtstart = f"DTSTART:{event.event_date.strftime('%Y%m%d')}T{event.event_time.strftime('%H%M%S')}"
        else:
            dtstart = f"DTSTART;VALUE=DATE:{event.event_date.strftime('%Y%m%d')}"
        lines += ["BEGIN:VEVENT", f"UID:event-{event.id}@clienttale", dtstart, f"SUMMARY:{_ics_escape(summary)}"]
        if event.description:
            lines.append(f"DESCRIPTION:{_ics_escape(event.description)}")
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")

    body = "\r\n".join(lines) + "\r\n"
    injured_name = f"{case.injured_first_name or ''} {case.injured_last_name or ''}".strip()
    filename_base = re.sub(r"[^A-Za-z0-9]+", "-", injured_name).strip("-") or case.case_number
    return Response(
        body,
        mimetype="text/calendar",
        headers={"Content-Disposition": f'attachment; filename="{filename_base}-events.ics"'},
    )


@cases_bp.post("/<int:case_id>/opposing-counsel")
@login_required
def add_opposing_counsel(case_id):
    case = Case.query.get_or_404(case_id)
    data = request.get_json(silent=True) or {}

    counsel = OpposingCounsel(
        case_id=case.id,
        name=(data.get("name") or "").strip() or None,
        firm=(data.get("firm") or "").strip() or None,
        phone=(data.get("phone") or "").strip() or None,
        email=(data.get("email") or "").strip() or None,
    )
    db.session.add(counsel)
    db.session.commit()
    return jsonify(counsel.to_dict()), 201


@cases_bp.put("/<int:case_id>/opposing-counsel/<int:counsel_id>")
@login_required
def update_opposing_counsel(case_id, counsel_id):
    counsel = OpposingCounsel.query.filter_by(id=counsel_id, case_id=case_id).first_or_404()
    data = request.get_json(silent=True) or {}
    for field in ("name", "firm", "phone", "email"):
        if field in data:
            setattr(counsel, field, (data.get(field) or "").strip() or None)
    db.session.commit()
    return jsonify(counsel.to_dict())


@cases_bp.delete("/<int:case_id>/opposing-counsel/<int:counsel_id>")
@login_required
def delete_opposing_counsel(case_id, counsel_id):
    counsel = OpposingCounsel.query.filter_by(id=counsel_id, case_id=case_id).first_or_404()
    db.session.delete(counsel)
    db.session.commit()
    return jsonify({"status": "deleted"})
