import io
import os
import re
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pymysql
from pypdf import PdfReader

app = FastAPI(title="ClientTale API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "clienttale")


def get_db_connection(with_db=True):
    retries = 15
    while retries > 0:
        try:
            kwargs = {
                "host": DB_HOST,
                "user": DB_USER,
                "password": DB_PASSWORD,
                "cursorclass": pymysql.cursors.DictCursor,
                "autocommit": True,
            }
            if with_db:
                kwargs["database"] = DB_NAME
            return pymysql.connect(**kwargs)
        except pymysql.err.OperationalError as e:
            retries -= 1
            print(f"Waiting for MySQL to start... ({retries} attempts left)")
            time.sleep(2)
    raise e


def init_db():
    conn = get_db_connection(with_db=False)
    with conn.cursor() as cursor:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    conn.close()

    conn = get_db_connection(with_db=True)
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS staff (
                id INT AUTO_INCREMENT PRIMARY KEY,
                full_name VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL,
                email VARCHAR(255) NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                id INT AUTO_INCREMENT PRIMARY KEY,
                case_number VARCHAR(100) NOT NULL,
                case_title VARCHAR(255) NOT NULL,
                type_of_case VARCHAR(100),
                status VARCHAR(50) DEFAULT 'Active',
                county VARCHAR(100),
                date_of_event DATE,
                date_of_contact DATE,
                sol_date DATE,
                name_of_injured VARCHAR(255),
                dob DATE,
                age INT,
                ssn VARCHAR(50),
                height VARCHAR(50),
                weight VARCHAR(50),
                dod DATE,
                client_name VARCHAR(255),
                work_phone VARCHAR(50),
                address TEXT,
                city_state_zip VARCHAR(255),
                country VARCHAR(100),
                email VARCHAR(255),
                lawyer_id INT,
                paralegal_id INT,
                legal_assistant VARCHAR(255),
                ref_primary VARCHAR(255),
                ref_secondary VARCHAR(255),
                judge VARCHAR(255),
                conf_check VARCHAR(255),
                date_declined DATE,
                who_declined VARCHAR(255),
                how_declined VARCHAR(255),
                synopsis TEXT,
                comments TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS case_dates (
                id INT AUTO_INCREMENT PRIMARY KEY,
                case_id INT,
                event_type VARCHAR(100),
                title VARCHAR(255),
                event_date DATETIME,
                timeframe VARCHAR(50),
                notes TEXT,
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
            )
        """)
    conn.close()


@app.on_event("startup")
def startup_event():
    init_db()


class CaseModel(BaseModel):
    case_number: str
    case_title: str
    type_of_case: Optional[str] = None
    status: Optional[str] = "Active"
    county: Optional[str] = None
    date_of_event: Optional[str] = None
    date_of_contact: Optional[str] = None
    sol_date: Optional[str] = None
    name_of_injured: Optional[str] = None
    dob: Optional[str] = None
    age: Optional[int] = None
    ssn: Optional[str] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    dod: Optional[str] = None
    client_name: Optional[str] = None
    work_phone: Optional[str] = None
    address: Optional[str] = None
    city_state_zip: Optional[str] = None
    country: Optional[str] = None
    email: Optional[str] = None
    lawyer_id: Optional[int] = None
    paralegal_id: Optional[int] = None
    legal_assistant: Optional[str] = None
    ref_primary: Optional[str] = None
    ref_secondary: Optional[str] = None
    judge: Optional[str] = None
    conf_check: Optional[str] = None
    date_declined: Optional[str] = None
    who_declined: Optional[str] = None
    how_declined: Optional[str] = None
    synopsis: Optional[str] = None
    comments: Optional[str] = None


class StaffModel(BaseModel):
    full_name: str
    role: str
    email: str


class DateModel(BaseModel):
    event_type: str
    title: str
    event_date: str
    notes: Optional[str] = None


@app.get("/api/staff")
def get_staff():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM staff")
        result = cursor.fetchall()
    conn.close()
    return result


@app.post("/api/staff")
def add_staff(staff: StaffModel):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO staff (full_name, role, email) VALUES (%s, %s, %s)",
            (staff.full_name, staff.role, staff.email),
        )
        staff_id = cursor.lastrowid
    conn.close()
    return {"id": staff_id, **staff.dict()}


@app.delete("/api/cases/{case_id}")
async def delete_case(case_id: int):
  conn = get_db_connection()
  try:
    with conn.cursor() as cursor:
      cursor.execute("SELECT id FROM cases WHERE id = %s", (case_id,))
      if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Case not found")

      cursor.execute("DELETE FROM cases WHERE id = %s", (case_id,))
      conn.commit()
    return {"status": "success", "message": f"Case {case_id} deleted"}
  except Exception as e:
    conn.rollback()
    raise HTTPException(status_code=500, detail=str(e))
  finally:
    conn.close()


@app.get("/api/cases")
def get_cases(q: Optional[str] = None):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        if q:
            query = """
                SELECT * FROM cases 
                WHERE case_number LIKE %s OR case_title LIKE %s OR name_of_injured LIKE %s OR client_name LIKE %s
            """
            like_q = f"%{q}%"
            cursor.execute(query, (like_q, like_q, like_q, like_q))
        else:
            cursor.execute("SELECT * FROM cases")
        cases = cursor.fetchall()
        for c in cases:
            cursor.execute(
                "SELECT * FROM case_dates WHERE case_id = %s", (c["id"],)
            )
            c["dates"] = cursor.fetchall()
    conn.close()
    return cases


@app.get("/api/cases/{case_id}")
def get_case(case_id: int):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM cases WHERE id = %s", (case_id,))
        case = cursor.fetchone()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        cursor.execute(
            "SELECT * FROM case_dates WHERE case_id = %s", (case_id,)
        )
        case["dates"] = cursor.fetchall()
    conn.close()
    return case


@app.post("/api/cases")
def add_case(case: CaseModel):
    conn = get_db_connection()
    data = case.dict()
    keys = list(data.keys())
    values = list(data.values())
    placeholders = ", ".join(["%s"] * len(keys))
    columns = ", ".join(keys)

    with conn.cursor() as cursor:
        query = f"INSERT INTO cases ({columns}) VALUES ({placeholders})"
        cursor.execute(query, values)
        case_id = cursor.lastrowid
    conn.close()
    return {"id": case_id, **data, "dates": []}


@app.put("/api/cases/{case_id}")
def update_case(case_id: int, case: CaseModel):
    conn = get_db_connection()
    data = case.dict()
    set_clause = ", ".join([f"{k} = %s" for k in data.keys()])
    values = list(data.values()) + [case_id]

    with conn.cursor() as cursor:
        query = f"UPDATE cases SET {set_clause} WHERE id = %s"
        cursor.execute(query, values)
    conn.close()
    return {"id": case_id, **data}


@app.post("/api/cases/{case_id}/dates")
def add_date(case_id: int, date_item: DateModel):
    event_dt = datetime.fromisoformat(date_item.event_date)
    timeframe = "Past" if event_dt < datetime.now() else "Upcoming"

    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO case_dates (case_id, event_type, title, event_date, timeframe, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
        """,
            (
                case_id,
                date_item.event_type,
                date_item.title,
                date_item.event_date,
                timeframe,
                date_item.notes,
            ),
        )
        date_id = cursor.lastrowid
    conn.close()
    return {"id": date_id, "timeframe": timeframe, **date_item.dict()}

@app.delete("/api/cases/{case_id}")
async def delete_case(case_id: int):
  conn = get_db_connection()
  try:
    with conn.cursor() as cursor:
      # Check existence
      cursor.execute("SELECT id FROM cases WHERE id = %s", (case_id,))
      if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Case not found")

      # Perform deletion
      cursor.execute("DELETE FROM cases WHERE id = %s", (case_id,))
      conn.commit()

    return {"status": "success", "message": f"Case {case_id} deleted"}
  except Exception as e:
    conn.rollback()
    raise HTTPException(status_code=500, detail=str(e))
  finally:
    conn.close()

FORM_KEYWORDS = [
    "Injured Person",
    "Name of Injured",
    "DOB",
    "DOD",
    "SSN",
    "Age",
    "Hgt",
    "Wgt",
    "Case Number",
    "Type of Case",
    "Date of Event",
    "Conf of Int Check",
    "Status of Case",
    "SOL Date",
    "Date of Contact",
    "County",
    "Referral Source",
    "Date Declined",
    "Who Declined",
    "How Declined",
    "Primary",
    "Secondary",
    "Legal Assistant",
    "Judge",
    "Client Name",
    "Address",
    "City, State, Zip",
    "Country",
    "Work phone",
    "E-mail",
    "Email",
    "Contact Data",
    "Assignments & Referrals",
    "OTOROWSKI",
    "INTAKE COMMENTS",
    "CASE SYNOPIS",
    "Page",
]


@app.post("/api/import-pdf")
async def import_pdf(file: UploadFile = File(...)):
  contents = await file.read()
  reader = PdfReader(io.BytesIO(contents))

  # Extract text with layout mode enabled if supported by pypdf
  extracted_text = ""
  for page in reader.pages:
    try:
      extracted_text += page.extract_text(extraction_mode="layout") + "\n"
    except Exception:
      extracted_text += (page.extract_text() or "") + "\n"

  def extract_field_value(label: str) -> Optional[str]:
    # Build stop-pattern using all other keywords
    other_keywords = [
        re.escape(k) for k in FORM_KEYWORDS if k.lower() != label.lower()
    ]
    stop_pattern = "|".join(other_keywords)

    pattern = rf"{re.escape(label)}\s*[:\|]?\s*(.*?)(?=(?:{stop_pattern})|[\r\n]{{2,}}|$)"
    match = re.search(pattern, extracted_text, re.IGNORECASE | re.DOTALL)
    if match:
      val = match.group(1).strip()
      # Clean up leading pipes or line breaks
      val = re.sub(r"^[\|\:\s]+", "", val).strip()
      # Take only first line if multi-line noise exists
      lines = [line.strip() for line in val.splitlines() if line.strip()]
      return lines[0] if lines else None
    return None

  def parse_date(date_str: Optional[str]) -> Optional[str]:
    if not date_str:
      return None
    match = re.search(r"\b(\d{1,2}/\d{1,2}/\d{4})\b", date_str)
    if match:
      date_str = match.group(1)
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y"):
      try:
        return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
      except ValueError:
        continue
    return None

  # Dedicated pattern extractors for distinct data types
  email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", extracted_text)
  extracted_email = email_match.group(0) if email_match else None

  phone_match = re.search(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", extracted_text)
  extracted_phone = phone_match.group(0) if phone_match else None

  # Case & Person Identifiers
  c_num = extract_field_value("Case Number") or "IMP-" + datetime.now().strftime(
      "%Y%m%d%H%M%S"
  )

  injured_first = extract_field_value("Name of Injured")
  injured_last = extract_field_value("Injured Person")
  if injured_first and injured_last and injured_last in injured_first:
    name_inj = injured_first
  else:
    name_inj = (
        f"{injured_first} {injured_last}".strip()
        if (injured_first and injured_last)
        else (injured_first or injured_last)
    )

  client_val = extract_field_value("Client Name") or name_inj

  # Address line parsing
  addr_raw = extract_field_value("Address")
  city_zip_match = re.search(
      r"([A-Za-z\s]+,?\s+[A-Z]{2}\s+\d{5})", extracted_text
  )
  city_state_zip = (
      city_zip_match.group(1) if city_zip_match else extract_field_value("City, State, Zip")
  )

  case_data = {
      "case_number": c_num,
      "case_title": f"Case: {client_val or c_num}",
      "type_of_case": extract_field_value("Type of Case"),
      "status": extract_field_value("Status of Case") or "Active",
      "county": extract_field_value("County"),
      "date_of_event": parse_date(extract_field_value("Date of Event")),
      "date_of_contact": parse_date(extract_field_value("Date of Contact")),
      "sol_date": parse_date(extract_field_value("SOL Date")),
      "name_of_injured": name_inj,
      "dob": parse_date(extract_field_value("DOB")),
      "age": (
          int(m.group(1))
          if (
              val := extract_field_value("Age")
          )
          and (m := re.search(r"\d+", val))
          else None
      ),
      "ssn": extract_field_value("SSN"),
      "height": extract_field_value("Hgt"),
      "weight": extract_field_value("Wgt"),
      "dod": parse_date(extract_field_value("DOD")),
      "client_name": client_val,
      "work_phone": extracted_phone or extract_field_value("Work phone"),
      "address": addr_raw,
      "city_state_zip": city_state_zip,
      "country": extract_field_value("Country"),
      "email": extracted_email or extract_field_value("E-mail"),
      "legal_assistant": extract_field_value("Legal Assistant"),
      "ref_primary": extract_field_value("Primary"),
      "ref_secondary": extract_field_value("Secondary"),
      "judge": extract_field_value("Judge"),
      "conf_check": parse_date(extract_field_value("Conf of Int Check")),
      "date_declined": parse_date(extract_field_value("Date Declined")),
      "who_declined": extract_field_value("Who Declined"),
      "how_declined": extract_field_value("How Declined"),
      "synopsis": extracted_text,
  }

  conn = get_db_connection()
  keys = list(case_data.keys())
  values = list(case_data.values())
  placeholders = ", ".join(["%s"] * len(keys))
  columns = ", ".join(keys)

  with conn.cursor() as cursor:
    query = f"INSERT INTO cases ({columns}) VALUES ({placeholders})"
    cursor.execute(query, values)
    case_id = cursor.lastrowid
  conn.commit()
  conn.close()

  return {"status": "success", "case_id": case_id}