from datetime import datetime

from app import db


class Staff(db.Model):
    __tablename__ = "staff"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.Enum("lawyer", "paralegal", "admin", name="staff_role"), nullable=False)
    email = db.Column(db.String(255))
    username = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name(),
            "role": self.role,
            "email": self.email,
            "username": self.username,
            "active": self.active,
        }


class Case(db.Model):
    __tablename__ = "cases"

    id = db.Column(db.Integer, primary_key=True)

    case_number = db.Column(db.String(50), nullable=False, unique=True)
    status = db.Column(db.String(50), nullable=False, default="Pending")
    case_type = db.Column(db.String(50))
    date_of_event = db.Column(db.Date)
    sol_date = db.Column(db.Date)
    conf_int_check_date = db.Column(db.Date)
    county = db.Column(db.String(100))
    judge = db.Column(db.String(255))

    primary_lawyer_id = db.Column(db.Integer, db.ForeignKey("staff.id", ondelete="SET NULL"))
    secondary_lawyer_id = db.Column(db.Integer, db.ForeignKey("staff.id", ondelete="SET NULL"))
    legal_assistant_id = db.Column(db.Integer, db.ForeignKey("staff.id", ondelete="SET NULL"))

    injured_first_name = db.Column(db.String(100))
    injured_last_name = db.Column(db.String(100))
    dob = db.Column(db.Date)
    dod = db.Column(db.Date)
    ssn = db.Column(db.String(20))
    age = db.Column(db.Integer)
    height = db.Column(db.String(20))
    weight = db.Column(db.String(20))

    client_first_name = db.Column(db.String(100))
    client_last_name = db.Column(db.String(100))
    address_line1 = db.Column(db.String(255))
    address_line2 = db.Column(db.String(255))
    city = db.Column(db.String(100))
    state = db.Column(db.String(20))
    zip = db.Column(db.String(20))
    country = db.Column(db.String(100))
    work_phone = db.Column(db.String(50))
    email = db.Column(db.String(255))

    case_synopsis = db.Column(db.Text)
    intake_comments = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    primary_lawyer = db.relationship("Staff", foreign_keys=[primary_lawyer_id])
    secondary_lawyer = db.relationship("Staff", foreign_keys=[secondary_lawyer_id])
    legal_assistant = db.relationship("Staff", foreign_keys=[legal_assistant_id])
    events = db.relationship(
        "CaseEvent", backref="case", cascade="all, delete-orphan", order_by="CaseEvent.event_date"
    )
    opposing_counsel = db.relationship(
        "OpposingCounsel", backref="case", cascade="all, delete-orphan", order_by="OpposingCounsel.id"
    )

    def to_dict(self, include_events=False):
        data = {
            "id": self.id,
            "case_number": self.case_number,
            "status": self.status,
            "case_type": self.case_type,
            "date_of_event": self.date_of_event.isoformat() if self.date_of_event else None,
            "sol_date": self.sol_date.isoformat() if self.sol_date else None,
            "conf_int_check_date": self.conf_int_check_date.isoformat() if self.conf_int_check_date else None,
            "county": self.county,
            "judge": self.judge,
            "primary_lawyer_id": self.primary_lawyer_id,
            "primary_lawyer_name": self.primary_lawyer.full_name() if self.primary_lawyer else None,
            "secondary_lawyer_id": self.secondary_lawyer_id,
            "secondary_lawyer_name": self.secondary_lawyer.full_name() if self.secondary_lawyer else None,
            "legal_assistant_id": self.legal_assistant_id,
            "legal_assistant_name": self.legal_assistant.full_name() if self.legal_assistant else None,
            "injured_first_name": self.injured_first_name,
            "injured_last_name": self.injured_last_name,
            "dob": self.dob.isoformat() if self.dob else None,
            "dod": self.dod.isoformat() if self.dod else None,
            "ssn": self.ssn,
            "age": self.age,
            "height": self.height,
            "weight": self.weight,
            "client_first_name": self.client_first_name,
            "client_last_name": self.client_last_name,
            "address_line1": self.address_line1,
            "address_line2": self.address_line2,
            "city": self.city,
            "state": self.state,
            "zip": self.zip,
            "country": self.country,
            "work_phone": self.work_phone,
            "email": self.email,
            "case_synopsis": self.case_synopsis,
            "intake_comments": self.intake_comments,
            "opposing_counsel": [oc.to_dict() for oc in self.opposing_counsel],
        }
        if include_events:
            data["events"] = [e.to_dict() for e in self.events]
        return data


class OpposingCounsel(db.Model):
    __tablename__ = "opposing_counsel"

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String(255))
    firm = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "case_id": self.case_id,
            "name": self.name,
            "firm": self.firm,
            "phone": self.phone,
            "email": self.email,
        }


class CaseEvent(db.Model):
    __tablename__ = "case_events"

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    event_type = db.Column(db.String(100), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    event_time = db.Column(db.Time)
    description = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "case_id": self.case_id,
            "event_type": self.event_type,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "event_time": self.event_time.strftime("%H:%M") if self.event_time else None,
            "description": self.description,
        }
