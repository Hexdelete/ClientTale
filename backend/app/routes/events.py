from datetime import date

from flask import Blueprint, jsonify, request

from app.auth_utils import login_required
from app.models import Case, CaseEvent

events_bp = Blueprint("events", __name__)


@events_bp.get("/events/upcoming")
@login_required
def upcoming_events():
    days = request.args.get("days", type=int)
    today = date.today()

    query = CaseEvent.query.join(Case).filter(CaseEvent.event_date >= today)
    if days:
        from datetime import timedelta

        query = query.filter(CaseEvent.event_date <= today + timedelta(days=days))
    query = query.order_by(CaseEvent.event_date.asc())

    results = []
    for event in query.all():
        payload = event.to_dict()
        payload["case_number"] = event.case.case_number
        payload["client_name"] = f"{event.case.client_first_name or ''} {event.case.client_last_name or ''}".strip()
        payload["status"] = event.case.status
        results.append(payload)
    return jsonify(results)
