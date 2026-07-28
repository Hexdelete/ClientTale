from datetime import datetime
import io
import os
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


@app.delete("/api/staff/{staff_id}")
def delete_staff(staff_id: int):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM staff WHERE id = %s", (staff_id,))
    conn.close()
    return {"status": "success"}


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


@app.post("/api/import-pdf")
async def import_pdf(file: UploadFile = File(...)):
    contents = await file.read()
    reader = PdfReader(io.BytesIO(contents))
    extracted_text = ""
    for page in reader.pages:
        extracted_text += (page.extract_text() or "") + "\n"

    # Default record populated with raw PDF text in synopsis
    case_data = {
        "case_number": "IMP-" + datetime.now().strftime("%Y%m%d%H%M%S"),
        "case_title": "Imported Intake Case",
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
    conn.close()
    return {"status": "success", "case_id": case_id}
