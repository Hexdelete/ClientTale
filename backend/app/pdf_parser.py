"""
Parses the FileMaker Pro "Case Intake Form" PDF used by the firm's intake
process. The layout is fixed (same label ordering on every export), so
fields are extracted by locating each label in the flattened page text and
slicing out the text between it and the next known label.
"""
import re

import pdfplumber

NOISE_PATTERNS = [
    r"Case Intake Form",
    r"OTOROWSKI\s*&?\s*",
    r"GOLDEN,?\s*PLLC",
    r"\bGOLDEN\b",
    r"Injured Person:\s*\S*",
    r"Case Data",
    r"Contact Data",
    r"\d+\s+Winslow Way West",
    r"Bainbridge Island,?\s*WA\s*\d*",
    r"Page \d+ of\s*\d*",
    r"DATE PRINTED:?[^A-Za-z]*",
    r"PAGE \d+",
    r"INTAKE COMMENTS AND RECOMMENDATION",
    r"C\s+S\s*",
    r"ASE\s+YNOPIS",
    r"What, when, where, who, how, why\.",
]

# Ordered as they appear on the form. Order matters: each label's value is
# whatever text sits between it and the next label found in the text.
LABELS = [
    "Name of Injured",
    "DOB",
    "DOD",
    "SSN",
    "Age",
    "Hgt",
    "Wgt",
    "Case Number",
    "Type of Case",
    "Status of Case",
    "Date of Event",
    "SOL Date",
    "Conf of Int Check",
    "Date of Contact",
    "Referral Source:",
    "County",
    "Primary",
    "Date Declined",
    "Secondary",
    "Who Declined?",
    "Legal Assistant",
    "How Declined?",
    "Judge",
    "Client Name",
    "Address",
    "City, State, Zip",
    "Country",
    "Work phone",
    "E-mail",
]


def _clean_text(text):
    t = text.replace("\n", " ")
    for pattern in NOISE_PATTERNS:
        t = re.sub(pattern, " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _extract_by_labels(text, labels):
    positions = []
    cursor = 0
    for label in labels:
        idx = text.find(label, cursor)
        positions.append(idx if idx != -1 else None)
        if idx != -1:
            cursor = idx + len(label)

    values = {}
    for i, label in enumerate(labels):
        if positions[i] is None:
            values[label] = ""
            continue
        start = positions[i] + len(label)
        end = len(text)
        for j in range(i + 1, len(labels)):
            if positions[j] is not None:
                end = positions[j]
                break
        values[label] = text[start:end].strip()
    return values


def _split_name(full_name, is_last_first=False):
    parts = full_name.split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def _to_iso_date(value):
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", value.strip())
    if not m:
        return None
    month, day, year = m.groups()
    return f"{year}-{int(month):02d}-{int(day):02d}"


def _clean_email(value):
    # PDF line-wraps long emails, leaving a stray space before the TLD
    # (e.g. "name@host.hotmail. com" -> "name@host.hotmail.com").
    return re.sub(r"\.\s+(?=[a-zA-Z]{2,}$)", ".", value.strip())


def _split_city_state_zip(value):
    m = re.match(r"^(.*?)\s+([A-Za-z]{2})\s+(\d{5}(?:-\d{4})?)$", value.strip())
    if not m:
        return value.strip(), "", ""
    return m.group(1).strip(), m.group(2).strip(), m.group(3).strip()


def parse_intake_pdf(file_stream):
    with pdfplumber.open(file_stream) as pdf:
        page1_text = pdf.pages[0].extract_text() or ""
        page2_text = pdf.pages[1].extract_text() if len(pdf.pages) > 1 else ""

    cleaned_page1 = _clean_text(page1_text)
    values = _extract_by_labels(cleaned_page1, LABELS)

    address_line1, address_line2 = "", ""
    address_raw = values.get("Address", "")
    if address_raw:
        # FileMaker prints line 1 then optional line 2 (e.g. "Apt G") run together
        # once newlines are flattened; split on common secondary-line prefixes.
        m = re.match(r"^(.*?)(?:\s+(Apt\.?\s*\S+|Suite\s*\S+|Unit\s*\S+|#\s*\S+))?$", address_raw)
        if m:
            address_line1 = m.group(1).strip()
            address_line2 = (m.group(2) or "").strip()
        else:
            address_line1 = address_raw

    city, state, zip_code = _split_city_state_zip(values.get("City, State, Zip", ""))

    injured_first, injured_last = _split_name(values.get("Name of Injured", ""))
    client_first, client_last = _split_name(values.get("Client Name", ""))

    age_raw = values.get("Age", "")
    age = int(age_raw) if age_raw.isdigit() else None

    # Case synopsis lives on page 2, after the "Case Synopsis" label block.
    case_synopsis = _clean_text(page2_text)

    parsed = {
        "injured_first_name": injured_first,
        "injured_last_name": injured_last,
        "dob": _to_iso_date(values.get("DOB", "")),
        "dod": _to_iso_date(values.get("DOD", "")),
        "ssn": values.get("SSN", "") or None,
        "age": age,
        "height": values.get("Hgt", "") or None,
        "weight": values.get("Wgt", "") or None,
        "case_number": values.get("Case Number", ""),
        "case_type": values.get("Type of Case", "") or None,
        "status": values.get("Status of Case", "") or "Pending",
        "date_of_event": _to_iso_date(values.get("Date of Event", "")),
        "sol_date": _to_iso_date(values.get("SOL Date", "")),
        "conf_int_check_date": _to_iso_date(values.get("Conf of Int Check", "")),
        "county": values.get("County", "") or None,
        "judge": values.get("Judge", "") or None,
        "client_first_name": client_first,
        "client_last_name": client_last,
        "address_line1": address_line1 or None,
        "address_line2": address_line2 or None,
        "city": city or None,
        "state": state or None,
        "zip": zip_code or None,
        "country": values.get("Country", "") or None,
        "work_phone": values.get("Work phone", "") or None,
        "email": _clean_email(values.get("E-mail", "")) or None,
        "case_synopsis": case_synopsis or None,
        # Staff names come back as free text; the frontend matches these
        # against the /api/staff dropdown options for the user to confirm.
        "primary_lawyer_name": values.get("Primary", "") or None,
        "secondary_lawyer_name": values.get("Secondary", "") or None,
        "legal_assistant_name": values.get("Legal Assistant", "") or None,
    }
    return parsed
