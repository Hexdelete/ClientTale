# ClientTale — Law Client Case Tracker

A self-hosted case tracker built entirely on open-source components, running as
Docker containers:

- **nginx** — serves the static frontend and reverse-proxies `/api/` to the backend
- **Flask (Python)** — REST API, session-based login, PDF intake parsing
- **MySQL 8** — case, staff, and event data

## Features

- Dashboard listing upcoming events across every case
- Live case search (by client, injured person, case number, status, county) with
  each matching case's upcoming events shown inline
- Manage Staff page to add/deactivate lawyers, paralegals, and admins, each
  with their own login — lawyers and paralegals populate the Primary/Secondary
  Lawyer and Legal Assistant dropdowns on every case file
- Full case file matching every field on the firm's FileMaker Pro intake form
- **Import From PDF** — upload the FileMaker-generated intake PDF and the case
  form is pre-filled automatically (staff names are matched against existing
  staff records for you to confirm before saving)

## Running it

1. Review `.env` and change the default passwords/secret key.
2. From this directory:

   ```
   docker compose up --build
   ```

3. Visit `http://localhost:8080` in a browser.
4. Sign in with the seeded admin account:
   - Username: `admin`
   - Password: `changeme123`

   **Change this password immediately** from the Manage Staff page (edit your
   own row, set a new password).

## Data model

See `db/init.sql` for the full schema:

- `staff` — every staff member (`role` = `lawyer`, `paralegal`, or `admin`),
  each with their own `username`/`password_hash` login
- `cases` — one row per case, with every field from the intake PDF plus
  `primary_lawyer_id` / `secondary_lawyer_id` / `legal_assistant_id` foreign
  keys into `staff`
- `case_events` — depositions, filings, hearings, deadlines, etc., each tied to
  a case and shown on the dashboard once their date arrives

## PDF import notes

The parser (`backend/app/pdf_parser.py`) is written against the fixed label
layout FileMaker Pro produces for this firm's "Case Intake Form." It locates
each known label in the extracted page text and slices out the value between
it and the next label. If the FileMaker layout changes, update the `LABELS`
list in that file to match the new field order.

Primary Lawyer, Secondary Lawyer, and Legal Assistant come back from the PDF
as plain names (not IDs) since the PDF has no concept of your staff directory.
The import review screen fuzzy-matches those names against your existing
staff list and lets you confirm/correct the dropdown selection — it never
creates new staff records automatically.

## Stopping / resetting

```
docker compose down          # stop containers, keep data
docker compose down -v       # stop containers and wipe the MySQL volume
```
