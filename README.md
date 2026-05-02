# ClinicPro — Patient Management System

**CS 348 Semester Project** | PostgreSQL + Flask + Vanilla JS

A full-stack clinic management system for managing patients, doctors, appointments, and prescriptions with dynamic reports.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Database** | PostgreSQL 18 (migrated from SQLite in Stage 3) |
| **Backend** | Python 3 / Flask |
| **Frontend** | HTML5, Vanilla CSS, Vanilla JS |
| **Driver** | psycopg2 (prepared statements with `%s` placeholders) |

## Features

- **CRUD Operations** — Full create, read, update, delete for Patients, Doctors, Appointments, and Prescriptions
- **Dynamic Dropdowns** — All select menus (departments, doctors, patients, appointments) are populated from the database at runtime
- **Filtered Reports** — Patient Report (age range, gender) and Appointment Report (date range, doctor, status) with dynamic filtering
- **Dashboard** — Real-time summary statistics (counts, scheduled/completed appointments)
- **Transfer Appointments** — Transactional multi-row operation to reassign all appointments from one doctor to another

---

## Stage 3 Deliverables

### 1. SQL Injection Protection (7%) — 4 Techniques

**Technique 1 — Prepared Statements** (all endpoints in [`app.py`](app.py)):
All queries use parameterized queries with `%s` placeholders. User input is never concatenated into SQL strings. See the docstring at the top of `app.py` for vulnerable vs. safe examples.

**Technique 2 — Input Sanitization** ([`sanitize.py`](sanitize.py)):
A dedicated validation module that sanitizes ALL user input BEFORE it reaches any SQL query:
- Names: reject empty, overlength, SQL comment sequences
- Emails: regex format validation
- Dates: strict YYYY-MM-DD format check
- Gender/Status: whitelist-only (reject anything not in allowed set)
- IDs: must be positive integers

**Technique 3 — Stored Procedures** ([`schema.sql`](schema.sql)):
PL/pgSQL functions encapsulate SQL logic server-side. Parameters are treated as variables, never as executable SQL:
- `sp_add_patient()` — INSERT patient via stored procedure
- `sp_transfer_appointments()` — atomic doctor transfer via stored procedure
- `sp_report_patients()` — filtered patient report via stored procedure

**Technique 4 — ORM / Object Relational Mapping** ([`models.py`](models.py)):
SQLAlchemy ORM maps Python classes to database tables. Instead of writing raw SQL, we use Python object operations — SQLAlchemy generates parameterized SQL internally:
- `get_patients` — uses `session.query(Patient).order_by(...)` instead of raw SQL
- `get_doctors` — uses `session.query(Doctor).order_by(...)` with automatic JOIN via relationship

### 2. Indexes (6%)
9 indexes in [`schema.sql`](schema.sql) — choosing the correct index type based on query pattern:

| Index | Type | Why |
|---|---|---|
| `idx_patients_dob` | **B+tree** | Range query: age filter uses `>=` and `<=` on date_of_birth |
| `idx_patients_name` | **B+tree** | Composite `ORDER BY last_name, first_name` |
| `idx_appointments_date` | **B+tree** | Range query: date filter uses `>=` and `<=` |
| `idx_patients_gender` | **Hash** | Point query: `WHERE gender = ?` |
| `idx_appointments_status` | **Hash** | Point query: `WHERE status = ?` |
| `idx_appointments_doctor` | **Hash** | Point query / JOIN: `WHERE doctor_id = ?` |
| `idx_appointments_patient` | **Hash** | JOIN: `ON a.patient_id = p.id` |
| `idx_doctors_department` | **Hash** | JOIN: `ON d.department_id = dep.id` |
| `idx_prescriptions_appointment` | **Hash** | JOIN: `ON pr.appointment_id = a.id` |

**Design rationale:** B+tree indexes are used for range queries and ORDER BY (leaf nodes form a linked list for sequential scanning). Hash indexes are used for pure equality/point queries (O(1) lookup). This is why we migrated from SQLite to PostgreSQL — SQLite only supports B+tree indexes.

### 3. Transactions & Isolation Levels (6%)
- All write operations use explicit `conn.commit()` / `conn.rollback()`
- **Transfer Appointments** endpoint (`/appointments/transfer`) uses `SERIALIZABLE` isolation level — the strongest level — ensuring the multi-row UPDATE is fully atomic and isolated
- Default isolation: `READ COMMITTED` (PostgreSQL default) — prevents dirty reads while allowing higher concurrency
- See [`database.py`](database.py) docstring for detailed isolation level discussion

### 4. AI Usage Disclosure (6%)

#### AI Tools Used

- **Antigravity (Google DeepMind)** — AI coding assistant used during development

#### Tasks AI Assisted With

1. **Code scaffolding** — Generating initial boilerplate for Flask routes, HTML templates, and JavaScript event handlers.
2. **SQL query writing** — Drafting complex JOIN queries for reports and dropdown endpoints.
3. **CSS styling** — Creating the visual design system (color variables, layout, responsive breakpoints).
4. **Database index design** — Suggesting which indexes to create (B+tree vs Hash) based on query patterns.
5. **PostgreSQL migration** — Converting from SQLite to PostgreSQL (SERIAL keys, %s placeholders, psycopg2 driver, EXTRACT/AGE functions).
6. **Transaction implementation** — Adding explicit COMMIT/ROLLBACK blocks and SERIALIZABLE isolation for the transfer appointments feature.
7. **Documentation** — Writing code comments explaining SQL injection protection, index justifications, and isolation level choices.
8. **Google Cloud Deployment** — Assisting with deploying the Flask application and PostgreSQL database to Google Cloud Platform.

#### How AI Output Was Verified and Modified

1. **Code review** — All AI-generated code was reviewed line-by-line before inclusion.
2. **Testing** — The application was tested locally by running the Flask dev server, performing CRUD operations, generating reports, and verifying the transfer appointments feature.
3. **Cross-referencing documentation** — AI suggestions were verified against:
   - [PostgreSQL documentation](https://www.postgresql.org/docs/) for index types (HASH vs BTREE), isolation levels, and transaction control
   - [psycopg2 documentation](https://www.psycopg.org/docs/) for connection parameters, cursor factories, and parameterized queries
   - [Flask documentation](https://flask.palletsprojects.com/) for route definitions and request handling
   - Course slides (Indexes_slides.pdf, SQLInCode_slides.pdf, TransactionsConcurrency_slides.pdf) for correct application of database concepts
4. **Bug fixes** — Several AI-generated queries and error handling paths were manually corrected during development.
5. **Design decisions** — The choice of B+tree vs Hash indexes, isolation levels, and the migration from SQLite to PostgreSQL were guided by course material and verified against official documentation.

---

## Setup & Run

### Prerequisites
- Python 3.8+
- PostgreSQL (with a database named `clinic_db` created)

### 1. Install dependencies
```bash
cd "CS 348 Project Part 2"
source venv/bin/activate
pip install flask psycopg2-binary
```

### 2. Configure database password
Edit `database.py` line 33 and set your PostgreSQL password, or:
```bash
export PGPASSWORD='your_password'
```

### 3. Initialize the database
In pgAdmin (or psql), run on the `clinic_db` database:
```bash
psql -U postgres -h 127.0.0.1 -d clinic_db -f schema.sql
psql -U postgres -h 127.0.0.1 -d clinic_db -f seed_data.sql
```

### 4. Run the application
```bash
source venv/bin/activate
python app.py
```
Open **http://localhost:5000**

---

## Project Structure

```
├── app.py              # Flask routes (CRUD, reports, transfer)
├── database.py         # PostgreSQL connection & init
├── schema.sql          # Tables + indexes (B+tree & Hash)
├── seed_data.sql       # Sample data (15 patients, 8 doctors, 20 appointments)
├── database_design.md  # ER diagram & normalization docs
├── templates/
│   └── index.html      # Single-page app HTML
├── static/
│   ├── app.js          # Frontend logic (CRUD, reports, transfer UI)
│   └── style.css       # Design system
└── venv/               # Python virtual environment
```

---

## Database Design

5 tables in **Third Normal Form (3NF)**:

```
departments ──< doctors ──< appointments >── patients
                               │
                          prescriptions
```

See [`database_design.md`](database_design.md) for full ER diagram and normalization discussion.
