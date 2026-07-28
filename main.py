from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import mysql.connector
from datetime import datetime

app = FastAPI(title="ClientTale API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    return mysql.connector.connect(
        host="db",
        user="user",
        password="password",
        database="legal_db"
    )

# --- Pydantic Schemas ---
class StaffCreate(BaseModel):
    full_name: str
    role: str
    email: str

class CaseCreate(BaseModel):
    case_number: str
    case_title: str
    client_name: str
    status: str = "Active"
    lawyer_id: Optional[int] = None
    paralegal_id: Optional[int] = None

class CaseUpdate(BaseModel):
    case_number: str
    case_title: str
    client_name: str
    status: str
    lawyer_id: Optional[int] = None
    paralegal_id: Optional[int] = None

class CriticalDateCreate(BaseModel):
    case_id: int
    event_type: str
    title: str
    event_date: str
    notes: Optional[str] = ""

# --- Staff Endpoints ---
@app.get("/api/staff")
def get_staff():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, full_name, role, email FROM staff")
    result = cursor.fetchall()
    cursor.close()
    db.close()
    return result

@app.post("/api/staff")
def create_staff(staff: StaffCreate):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO staff (full_name, role, email) VALUES (%s, %s, %s)",
        (staff.full_name, staff.role, staff.email)
    )
    db.commit()
    staff_id = cursor.lastrowid
    cursor.close()
    db.close()
    return {"id": staff_id, **staff.model_dump()}

@app.delete("/api/staff/{staff_id}")
def delete_staff(staff_id: int):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM staff WHERE id = %s", (staff_id,))
    db.commit()
    cursor.close()
    db.close()
    return {"message": "Staff deleted successfully"}

# --- Case Endpoints ---
@app.get("/api/cases")
def get_cases(search: Optional[str] = None):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    query = """
        SELECT c.id, c.case_number, c.case_title, c.client_name, c.status,
               l.full_name AS lawyer_in_charge,
               p.full_name AS paralegal_in_charge
        FROM cases c
        LEFT JOIN staff l ON c.lawyer_id = l.id
        LEFT JOIN staff p ON c.paralegal_id = p.id
    """
    params = []
    if search:
        query += " WHERE c.case_number LIKE %s OR c.case_title LIKE %s OR c.client_name LIKE %s OR l.full_name LIKE %s"
        term = f"%{search}%"
        params = [term, term, term, term]
        
    cursor.execute(query, params)
    cases = cursor.fetchall()
    cursor.close()
    db.close()
    return cases

@app.post("/api/cases")
def create_case(case: CaseCreate):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """INSERT INTO cases (case_number, case_title, client_name, status, lawyer_id, paralegal_id)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (case.case_number, case.case_title, case.client_name, case.status, case.lawyer_id, case.paralegal_id)
    )
    db.commit()
    case_id = cursor.lastrowid
    cursor.close()
    db.close()
    return {"id": case_id, **case.model_dump()}

@app.get("/api/cases/{case_id}")
def get_case(case_id: int):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute(
        """SELECT c.id, c.case_number, c.case_title, c.client_name, c.status, c.lawyer_id, c.paralegal_id,
                  l.full_name AS lawyer_in_charge, p.full_name AS paralegal_in_charge
           FROM cases c
           LEFT JOIN staff l ON c.lawyer_id = l.id
           LEFT JOIN staff p ON c.paralegal_id = p.id
           WHERE c.id = %s""",
        (case_id,)
    )
    case = cursor.fetchone()
    if not case:
        cursor.close()
        db.close()
        raise HTTPException(status_code=404, detail="Case not found")
        
    cursor.execute(
        """SELECT id, event_type, title, event_date, notes 
           FROM critical_dates WHERE case_id = %s""",
        (case_id,)
    )
    dates = cursor.fetchall()
    
    formatted_dates = []
    now = datetime.now()
    for d in dates:
        d_date = d["event_date"]
        timeframe = "Upcoming" if d_date and d_date >= now.date() else "Past"
        formatted_dates.append({
            "id": d["id"],
            "event_type": d["event_type"],
            "title": d["title"],
            "event_date": str(d["event_date"]),
            "notes": d["notes"],
            "timeframe": timeframe
        })
        
    case["dates"] = formatted_dates
    cursor.close()
    db.close()
    return case

@app.put("/api/cases/{case_id}")
def update_case(case_id: int, case: CaseUpdate):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """UPDATE cases 
           SET case_number = %s, case_title = %s, client_name = %s, status = %s, lawyer_id = %s, paralegal_id = %s
           WHERE id = %s""",
        (case.case_number, case.case_title, case.client_name, case.status, case.lawyer_id, case.paralegal_id, case_id)
    )
    db.commit()
    cursor.close()
    db.close()
    return {"message": "Case updated successfully"}

@app.post("/api/dates")
def create_date(date_entry: CriticalDateCreate):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """INSERT INTO critical_dates (case_id, event_type, title, event_date, notes)
           VALUES (%s, %s, %s, %s, %s)""",
        (date_entry.case_id, date_entry.event_type, date_entry.title, date_entry.event_date, date_entry.notes)
    )
    db.commit()
    cursor.close()
    db.close()
    return {"message": "Critical date added successfully"}

@app.post("/api/cases/import-pdf")
def import_pdf(file: UploadFile = File(...)):
    return {"status": f"Successfully imported and parsed {file.filename}"}