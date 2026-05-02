"""
CS 348 Project — Clinic Patient Management System (PostgreSQL)

═══ STAGE 3: SQL INJECTION PROTECTION (3 Techniques) ═══

TECHNIQUE 1 — PREPARED STATEMENTS (parameterized queries):
  All queries use %s placeholders. User input is NEVER concatenated into SQL.
  Vulnerable (NOT used):  "SELECT ... WHERE name = '" + input + "'"
  Safe (used throughout):  cur.execute("SELECT ... WHERE name = %s", (input,))
  Reference: SQLInCode_slides.pdf — SQL Injection, Prepared Statements

TECHNIQUE 2 — INPUT SANITIZATION (defense-in-depth):
  All user input is validated/sanitized in sanitize.py BEFORE reaching any query.
  - Names: reject empty, overlength, SQL comment sequences
  - Emails: regex format validation
  - Dates: strict YYYY-MM-DD format check
  - Gender/Status: whitelist-only (reject anything not in allowed set)
  - IDs: must be positive integers
  Reference: SQLInCode_slides.pdf — Input Sanitization

TECHNIQUE 3 — STORED PROCEDURES (server-side SQL encapsulation):
  Key operations use PL/pgSQL functions defined in schema.sql:
  - sp_add_patient(): INSERT patient via stored procedure
  - sp_transfer_appointments(): atomic doctor transfer via stored procedure
  - sp_report_patients(): filtered patient report via stored procedure
  Parameters are PL/pgSQL variables — PostgreSQL never interprets them as SQL.
  Reference: SQLInCode_slides.pdf — Stored Procedures, Database-Access Approaches

TECHNIQUE 4 — ORM (Object Relational Mapping via SQLAlchemy):
  ORM models in models.py map Python classes to database tables.
  Instead of writing SQL, we use Python object operations:
    Raw SQL: cur.execute("SELECT * FROM patients WHERE id = %s", (id,))
    ORM:     session.query(Patient).filter(Patient.id == id).first()
  SQLAlchemy generates parameterized SQL internally — user input never
  touches raw SQL strings. Used for: get_patients, get_doctors endpoints.
  Reference: SQLInCode_slides.pdf — ORM, Database-Access Approaches

═══ STAGE 3: TRANSACTIONS ═══
Explicit BEGIN/COMMIT/ROLLBACK for write operations. PostgreSQL isolation levels:
- READ COMMITTED (default): prevents dirty reads, allows more concurrency
- SERIALIZABLE: used for transfer_appointments (multi-row atomicity)

Reference: TransactionsConcurrency_slides.pdf — ACID, Isolation Levels, S2PL
"""

from flask import Flask, request, jsonify, render_template
from database import get_db, init_db
from sanitize import (sanitize_name, sanitize_email, sanitize_phone,
                      sanitize_date, sanitize_gender, sanitize_status,
                      sanitize_id, sanitize_time, sanitize_text, ValidationError)
from models import (Patient, Doctor, Department, Appointment, Prescription,
                    get_session)
import psycopg2.extras

app = Flask(__name__)


def dict_cursor(conn):
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


# ─── Page Routes ───────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')


# ─── Patient Routes ───────────────────────────────────────────
@app.route('/patients', methods=['GET'])
def get_patients():
    """TECHNIQUE 4 (ORM): Uses SQLAlchemy ORM to query patients.
    SQLAlchemy generates: SELECT ... FROM patients ORDER BY last_name, first_name
    No raw SQL written — ORM builds parameterized queries internally."""
    session = get_session()
    try:
        patients = session.query(Patient).order_by(Patient.last_name, Patient.first_name).all()
        result = [p.to_dict() for p in patients]
        session.close()
        return jsonify(result)
    except Exception as e:
        session.close()
        return jsonify({'error': str(e)}), 500


@app.route('/patients', methods=['POST'])
def add_patient():
    """TECHNIQUE 2 (Input Sanitization) + TECHNIQUE 3 (Stored Procedure):
    1. Sanitize all input fields via sanitize.py
    2. Call sp_add_patient() stored procedure (defined in schema.sql)
    """
    data = request.json
    try:
        # TECHNIQUE 2: Input Sanitization — validate before any DB call
        first_name = sanitize_name(data.get('first_name'), "First name")
        last_name = sanitize_name(data.get('last_name'), "Last name")
        dob = sanitize_date(data.get('date_of_birth'), "Date of birth")
        gender = sanitize_gender(data.get('gender'))
        phone = sanitize_phone(data.get('phone', ''))
        email = sanitize_email(data.get('email', ''))
        address = sanitize_text(data.get('address', ''), "Address")
    except ValidationError as ve:
        return jsonify({'error': str(ve)}), 400

    conn = get_db()
    cur = dict_cursor(conn)
    try:
        # TECHNIQUE 3: Stored Procedure — sp_add_patient handles INSERT server-side
        # TECHNIQUE 1: Prepared Statement — %s placeholders for all parameters
        cur.execute(
            "SELECT * FROM sp_add_patient(%s, %s, %s, %s, %s, %s, %s)",
            (first_name, last_name, dob, gender, phone, email, address)
        )
        patient = cur.fetchone()
        conn.commit()
        patient['date_of_birth'] = str(patient['date_of_birth'])
        cur.close(); conn.close()
        return jsonify(patient), 201
    except Exception as e:
        conn.rollback(); cur.close(); conn.close()
        return jsonify({'error': str(e)}), 400


@app.route('/patients/<int:patient_id>', methods=['PUT'])
def update_patient(patient_id):
    """TECHNIQUE 2 (Input Sanitization) + TECHNIQUE 1 (Prepared Statements)."""
    data = request.json
    try:
        # TECHNIQUE 2: Input Sanitization
        first_name = sanitize_name(data.get('first_name'), "First name")
        last_name = sanitize_name(data.get('last_name'), "Last name")
        dob = sanitize_date(data.get('date_of_birth'), "Date of birth")
        gender = sanitize_gender(data.get('gender'))
        phone = sanitize_phone(data.get('phone', ''))
        email = sanitize_email(data.get('email', ''))
        address = sanitize_text(data.get('address', ''), "Address")
    except ValidationError as ve:
        return jsonify({'error': str(ve)}), 400

    conn = get_db()
    cur = dict_cursor(conn)
    try:
        # TECHNIQUE 1: Prepared Statement
        cur.execute(
            "UPDATE patients SET first_name=%s, last_name=%s, date_of_birth=%s, gender=%s, phone=%s, email=%s, address=%s WHERE id=%s",
            (first_name, last_name, dob, gender, phone, email, address, patient_id)
        )
        conn.commit()
        cur.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
        patient = cur.fetchone()
        cur.close(); conn.close()
        if patient:
            patient['date_of_birth'] = str(patient['date_of_birth'])
            return jsonify(patient)
        return jsonify({'error': 'Patient not found'}), 404
    except Exception as e:
        conn.rollback(); cur.close(); conn.close()
        return jsonify({'error': str(e)}), 400


@app.route('/patients/<int:patient_id>', methods=['DELETE'])
def delete_patient(patient_id):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM patients WHERE id = %s", (patient_id,))
        if cur.rowcount == 0:
            conn.rollback(); cur.close(); conn.close()
            return jsonify({'error': 'Patient not found'}), 404
        conn.commit(); cur.close(); conn.close()
        return jsonify({'message': 'Patient deleted successfully'})
    except Exception as e:
        conn.rollback(); cur.close(); conn.close()
        return jsonify({'error': str(e)}), 400


# ─── Doctor Routes ─────────────────────────────────────────────
@app.route('/doctors', methods=['GET'])
def get_doctors():
    """TECHNIQUE 4 (ORM): Uses SQLAlchemy ORM to query doctors with department join.
    SQLAlchemy generates: SELECT ... FROM doctors JOIN departments ... ORDER BY ...
    The JOIN is handled automatically via the ORM relationship."""
    session = get_session()
    try:
        doctors = session.query(Doctor).order_by(Doctor.last_name, Doctor.first_name).all()
        result = [d.to_dict() for d in doctors]
        session.close()
        return jsonify(result)
    except Exception as e:
        session.close()
        return jsonify({'error': str(e)}), 500


@app.route('/doctors', methods=['POST'])
def add_doctor():
    """TECHNIQUE 2 (Input Sanitization) + TECHNIQUE 1 (Prepared Statements)."""
    data = request.json
    try:
        # TECHNIQUE 2: Input Sanitization
        first_name = sanitize_name(data.get('first_name'), "First name")
        last_name = sanitize_name(data.get('last_name'), "Last name")
        specialization = sanitize_name(data.get('specialization'), "Specialization")
        phone = sanitize_phone(data.get('phone', ''))
        email = sanitize_email(data.get('email', ''))
        department_id = sanitize_id(data.get('department_id'), "Department ID")
    except ValidationError as ve:
        return jsonify({'error': str(ve)}), 400

    conn = get_db()
    cur = dict_cursor(conn)
    try:
        # TECHNIQUE 1: Prepared Statement
        cur.execute(
            "INSERT INTO doctors (first_name, last_name, specialization, phone, email, department_id) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
            (first_name, last_name, specialization, phone, email, department_id)
        )
        doctor_id = cur.fetchone()['id']
        conn.commit()
        cur.execute("""SELECT d.*, dep.name as department_name FROM doctors d
               JOIN departments dep ON d.department_id = dep.id WHERE d.id = %s""", (doctor_id,))
        doctor = cur.fetchone()
        cur.close(); conn.close()
        return jsonify(doctor), 201
    except Exception as e:
        conn.rollback(); cur.close(); conn.close()
        return jsonify({'error': str(e)}), 400


@app.route('/doctors/<int:doctor_id>', methods=['PUT'])
def update_doctor(doctor_id):
    """TECHNIQUE 2 (Input Sanitization) + TECHNIQUE 1 (Prepared Statements)."""
    data = request.json
    try:
        # TECHNIQUE 2: Input Sanitization
        first_name = sanitize_name(data.get('first_name'), "First name")
        last_name = sanitize_name(data.get('last_name'), "Last name")
        specialization = sanitize_name(data.get('specialization'), "Specialization")
        phone = sanitize_phone(data.get('phone', ''))
        email = sanitize_email(data.get('email', ''))
        department_id = sanitize_id(data.get('department_id'), "Department ID")
    except ValidationError as ve:
        return jsonify({'error': str(ve)}), 400

    conn = get_db()
    cur = dict_cursor(conn)
    try:
        # TECHNIQUE 1: Prepared Statement
        cur.execute(
            "UPDATE doctors SET first_name=%s, last_name=%s, specialization=%s, phone=%s, email=%s, department_id=%s WHERE id=%s",
            (first_name, last_name, specialization, phone, email, department_id, doctor_id)
        )
        conn.commit()
        cur.execute("""SELECT d.*, dep.name as department_name FROM doctors d
               JOIN departments dep ON d.department_id = dep.id WHERE d.id = %s""", (doctor_id,))
        doctor = cur.fetchone()
        cur.close(); conn.close()
        if doctor:
            return jsonify(doctor)
        return jsonify({'error': 'Doctor not found'}), 404
    except Exception as e:
        conn.rollback(); cur.close(); conn.close()
        return jsonify({'error': str(e)}), 400


@app.route('/doctors/<int:doctor_id>', methods=['DELETE'])
def delete_doctor(doctor_id):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM doctors WHERE id = %s", (doctor_id,))
        if cur.rowcount == 0:
            conn.rollback(); cur.close(); conn.close()
            return jsonify({'error': 'Doctor not found'}), 404
        conn.commit(); cur.close(); conn.close()
        return jsonify({'message': 'Doctor deleted successfully'})
    except Exception as e:
        conn.rollback(); cur.close(); conn.close()
        return jsonify({'error': str(e)}), 400


# ─── Appointment Routes ────────────────────────────────────────
@app.route('/appointments', methods=['GET'])
def get_appointments():
    conn = get_db()
    cur = dict_cursor(conn)
    cur.execute("""SELECT a.id, a.patient_id, a.doctor_id, a.appointment_date, a.appointment_time,
                  a.status, a.notes,
                  p.first_name || ' ' || p.last_name as patient_name,
                  d.first_name || ' ' || d.last_name as doctor_name
           FROM appointments a
           JOIN patients p ON a.patient_id = p.id
           JOIN doctors d ON a.doctor_id = d.id
           ORDER BY a.appointment_date DESC, a.appointment_time DESC""")
    appts = cur.fetchall()
    for a in appts:
        if a.get('appointment_date'):
            a['appointment_date'] = str(a['appointment_date'])
    cur.close(); conn.close()
    return jsonify(appts)


@app.route('/appointments', methods=['POST'])
def add_appointment():
    """TECHNIQUE 2 (Input Sanitization) + TECHNIQUE 1 (Prepared Statements)."""
    data = request.json
    try:
        # TECHNIQUE 2: Input Sanitization
        patient_id = sanitize_id(data.get('patient_id'), "Patient ID")
        doctor_id = sanitize_id(data.get('doctor_id'), "Doctor ID")
        appt_date = sanitize_date(data.get('appointment_date'), "Appointment date")
        appt_time = sanitize_time(data.get('appointment_time'), "Appointment time")
        status = sanitize_status(data.get('status', 'Scheduled'))
        notes = sanitize_text(data.get('notes', ''), "Notes")
    except ValidationError as ve:
        return jsonify({'error': str(ve)}), 400

    conn = get_db()
    cur = dict_cursor(conn)
    try:
        # TECHNIQUE 1: Prepared Statement
        cur.execute(
            "INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, status, notes) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
            (patient_id, doctor_id, appt_date, appt_time, status, notes)
        )
        appt_id = cur.fetchone()['id']
        conn.commit()
        cur.execute("""SELECT a.*, p.first_name || ' ' || p.last_name as patient_name,
                      d.first_name || ' ' || d.last_name as doctor_name
               FROM appointments a JOIN patients p ON a.patient_id = p.id
               JOIN doctors d ON a.doctor_id = d.id WHERE a.id = %s""", (appt_id,))
        appt = cur.fetchone()
        appt['appointment_date'] = str(appt['appointment_date'])
        cur.close(); conn.close()
        return jsonify(appt), 201
    except Exception as e:
        conn.rollback(); cur.close(); conn.close()
        return jsonify({'error': str(e)}), 400


@app.route('/appointments/<int:appt_id>', methods=['PUT'])
def update_appointment(appt_id):
    """TECHNIQUE 2 (Input Sanitization) + TECHNIQUE 1 (Prepared Statements)."""
    data = request.json
    try:
        # TECHNIQUE 2: Input Sanitization
        patient_id = sanitize_id(data.get('patient_id'), "Patient ID")
        doctor_id = sanitize_id(data.get('doctor_id'), "Doctor ID")
        appt_date = sanitize_date(data.get('appointment_date'), "Appointment date")
        appt_time = sanitize_time(data.get('appointment_time'), "Appointment time")
        status = sanitize_status(data.get('status', 'Scheduled'))
        notes = sanitize_text(data.get('notes', ''), "Notes")
    except ValidationError as ve:
        return jsonify({'error': str(ve)}), 400

    conn = get_db()
    cur = dict_cursor(conn)
    try:
        # TECHNIQUE 1: Prepared Statement
        cur.execute(
            "UPDATE appointments SET patient_id=%s, doctor_id=%s, appointment_date=%s, appointment_time=%s, status=%s, notes=%s WHERE id=%s",
            (patient_id, doctor_id, appt_date, appt_time, status, notes, appt_id)
        )
        conn.commit()
        cur.execute("""SELECT a.*, p.first_name || ' ' || p.last_name as patient_name,
                      d.first_name || ' ' || d.last_name as doctor_name
               FROM appointments a JOIN patients p ON a.patient_id = p.id
               JOIN doctors d ON a.doctor_id = d.id WHERE a.id = %s""", (appt_id,))
        appt = cur.fetchone()
        cur.close(); conn.close()
        if appt:
            appt['appointment_date'] = str(appt['appointment_date'])
            return jsonify(appt)
        return jsonify({'error': 'Appointment not found'}), 404
    except Exception as e:
        conn.rollback(); cur.close(); conn.close()
        return jsonify({'error': str(e)}), 400


@app.route('/appointments/<int:appt_id>', methods=['DELETE'])
def delete_appointment(appt_id):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM appointments WHERE id = %s", (appt_id,))
        if cur.rowcount == 0:
            conn.rollback(); cur.close(); conn.close()
            return jsonify({'error': 'Appointment not found'}), 404
        conn.commit(); cur.close(); conn.close()
        return jsonify({'message': 'Appointment deleted successfully'})
    except Exception as e:
        conn.rollback(); cur.close(); conn.close()
        return jsonify({'error': str(e)}), 400


# ─── Prescription Routes ──────────────────────────────────────
@app.route('/prescriptions', methods=['GET'])
def get_prescriptions():
    conn = get_db()
    cur = dict_cursor(conn)
    cur.execute("""SELECT pr.id, pr.appointment_id, pr.medication, pr.dosage, pr.duration, pr.notes,
                  a.appointment_date,
                  p.first_name || ' ' || p.last_name as patient_name,
                  d.first_name || ' ' || d.last_name as doctor_name
           FROM prescriptions pr
           JOIN appointments a ON pr.appointment_id = a.id
           JOIN patients p ON a.patient_id = p.id
           JOIN doctors d ON a.doctor_id = d.id
           ORDER BY a.appointment_date DESC""")
    prescriptions = cur.fetchall()
    for pr in prescriptions:
        if pr.get('appointment_date'):
            pr['appointment_date'] = str(pr['appointment_date'])
    cur.close(); conn.close()
    return jsonify(prescriptions)


@app.route('/prescriptions', methods=['POST'])
def add_prescription():
    """TECHNIQUE 2 (Input Sanitization) + TECHNIQUE 1 (Prepared Statements)."""
    data = request.json
    try:
        # TECHNIQUE 2: Input Sanitization
        appointment_id = sanitize_id(data.get('appointment_id'), "Appointment ID")
        medication = sanitize_name(data.get('medication'), "Medication")
        dosage = sanitize_text(data.get('dosage', ''), "Dosage", max_length=100)
        duration = sanitize_text(data.get('duration', ''), "Duration", max_length=100)
        notes = sanitize_text(data.get('notes', ''), "Notes")
    except ValidationError as ve:
        return jsonify({'error': str(ve)}), 400

    conn = get_db()
    cur = dict_cursor(conn)
    try:
        # TECHNIQUE 1: Prepared Statement
        cur.execute(
            "INSERT INTO prescriptions (appointment_id, medication, dosage, duration, notes) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (appointment_id, medication, dosage, duration, notes)
        )
        presc_id = cur.fetchone()['id']
        conn.commit()
        cur.execute("""SELECT pr.*, a.appointment_date,
                      p.first_name || ' ' || p.last_name as patient_name,
                      d.first_name || ' ' || d.last_name as doctor_name
               FROM prescriptions pr JOIN appointments a ON pr.appointment_id = a.id
               JOIN patients p ON a.patient_id = p.id
               JOIN doctors d ON a.doctor_id = d.id WHERE pr.id = %s""", (presc_id,))
        presc = cur.fetchone()
        presc['appointment_date'] = str(presc['appointment_date'])
        cur.close(); conn.close()
        return jsonify(presc), 201
    except Exception as e:
        conn.rollback(); cur.close(); conn.close()
        return jsonify({'error': str(e)}), 400


@app.route('/prescriptions/<int:presc_id>', methods=['PUT'])
def update_prescription(presc_id):
    """TECHNIQUE 2 (Input Sanitization) + TECHNIQUE 1 (Prepared Statements)."""
    data = request.json
    try:
        # TECHNIQUE 2: Input Sanitization
        appointment_id = sanitize_id(data.get('appointment_id'), "Appointment ID")
        medication = sanitize_name(data.get('medication'), "Medication")
        dosage = sanitize_text(data.get('dosage', ''), "Dosage", max_length=100)
        duration = sanitize_text(data.get('duration', ''), "Duration", max_length=100)
        notes = sanitize_text(data.get('notes', ''), "Notes")
    except ValidationError as ve:
        return jsonify({'error': str(ve)}), 400

    conn = get_db()
    cur = dict_cursor(conn)
    try:
        # TECHNIQUE 1: Prepared Statement
        cur.execute(
            "UPDATE prescriptions SET appointment_id=%s, medication=%s, dosage=%s, duration=%s, notes=%s WHERE id=%s",
            (appointment_id, medication, dosage, duration, notes, presc_id)
        )
        conn.commit()
        cur.execute("""SELECT pr.*, a.appointment_date,
                      p.first_name || ' ' || p.last_name as patient_name,
                      d.first_name || ' ' || d.last_name as doctor_name
               FROM prescriptions pr JOIN appointments a ON pr.appointment_id = a.id
               JOIN patients p ON a.patient_id = p.id
               JOIN doctors d ON a.doctor_id = d.id WHERE pr.id = %s""", (presc_id,))
        presc = cur.fetchone()
        cur.close(); conn.close()
        if presc:
            presc['appointment_date'] = str(presc['appointment_date'])
            return jsonify(presc)
        return jsonify({'error': 'Prescription not found'}), 404
    except Exception as e:
        conn.rollback(); cur.close(); conn.close()
        return jsonify({'error': str(e)}), 400


@app.route('/prescriptions/<int:presc_id>', methods=['DELETE'])
def delete_prescription(presc_id):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM prescriptions WHERE id = %s", (presc_id,))
        if cur.rowcount == 0:
            conn.rollback(); cur.close(); conn.close()
            return jsonify({'error': 'Prescription not found'}), 404
        conn.commit(); cur.close(); conn.close()
        return jsonify({'message': 'Prescription deleted successfully'})
    except Exception as e:
        conn.rollback(); cur.close(); conn.close()
        return jsonify({'error': str(e)}), 400


# ─── Dynamic Dropdown API Endpoints ───────────────────────────
@app.route('/api/departments', methods=['GET'])
def get_departments():
    conn = get_db()
    cur = dict_cursor(conn)
    cur.execute("SELECT id, name, description FROM departments ORDER BY name")
    departments = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(departments)


@app.route('/api/doctors', methods=['GET'])
def get_doctors_dropdown():
    conn = get_db()
    cur = dict_cursor(conn)
    cur.execute("""SELECT d.id, d.first_name || ' ' || d.last_name as name, d.specialization, dep.name as department
           FROM doctors d JOIN departments dep ON d.department_id = dep.id ORDER BY d.last_name""")
    doctors = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(doctors)


@app.route('/api/patients', methods=['GET'])
def get_patients_dropdown():
    conn = get_db()
    cur = dict_cursor(conn)
    cur.execute("SELECT id, first_name || ' ' || last_name as name FROM patients ORDER BY last_name")
    patients = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(patients)


@app.route('/api/appointments', methods=['GET'])
def get_appointments_dropdown():
    conn = get_db()
    cur = dict_cursor(conn)
    cur.execute("""SELECT a.id, a.appointment_date || ' - ' || p.first_name || ' ' || p.last_name || ' with Dr. ' || d.last_name as label
           FROM appointments a
           JOIN patients p ON a.patient_id = p.id
           JOIN doctors d ON a.doctor_id = d.id
           ORDER BY a.appointment_date DESC""")
    appointments = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(appointments)


# ─── Report Routes ─────────────────────────────────────────────
@app.route('/reports/patients', methods=['GET'])
def report_patients():
    """TECHNIQUE 3 (Stored Procedure) + TECHNIQUE 1 (Prepared Statements):
    Calls sp_report_patients() — all filtering logic is encapsulated server-side.
    NULL parameters mean "no filter". Uses idx_patients_dob (BTREE) for range
    filtering and idx_patients_gender (HASH) for equality filtering."""
    min_age = request.args.get('min_age', type=int)
    max_age = request.args.get('max_age', type=int)
    gender = request.args.get('gender', '') or None  # Convert empty string to NULL

    conn = get_db()
    cur = dict_cursor(conn)
    # TECHNIQUE 3: Stored Procedure — sp_report_patients handles all filtering
    # TECHNIQUE 1: Prepared Statement — %s placeholders for parameters
    cur.execute(
        "SELECT * FROM sp_report_patients(%s, %s, %s)",
        (min_age, max_age, gender)
    )
    patients = cur.fetchall()
    for p in patients:
        if p.get('date_of_birth'):
            p['date_of_birth'] = str(p['date_of_birth'])
    cur.close(); conn.close()
    return jsonify(patients)


@app.route('/reports/appointments', methods=['GET'])
def report_appointments():
    """Filter appointments by date range, doctor, and/or status.
    Uses idx_appointments_date (BTREE) for range, idx_appointments_doctor (HASH)
    and idx_appointments_status (HASH) for equality filtering."""
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    doctor_id = request.args.get('doctor_id', type=int)
    status = request.args.get('status', '')

    query = """
        SELECT a.id, a.appointment_date, a.appointment_time, a.status, a.notes,
               p.first_name || ' ' || p.last_name as patient_name,
               p.phone as patient_phone,
               d.first_name || ' ' || d.last_name as doctor_name,
               dep.name as department
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN doctors d ON a.doctor_id = d.id
        JOIN departments dep ON d.department_id = dep.id
        WHERE 1=1
    """
    params = []
    if start_date:
        query += " AND a.appointment_date >= %s"
        params.append(start_date)
    if end_date:
        query += " AND a.appointment_date <= %s"
        params.append(end_date)
    if doctor_id:
        query += " AND a.doctor_id = %s"
        params.append(doctor_id)
    if status:
        query += " AND a.status = %s"
        params.append(status)

    query += " ORDER BY a.appointment_date DESC, a.appointment_time DESC"

    conn = get_db()
    cur = dict_cursor(conn)
    cur.execute(query, params)
    appts = cur.fetchall()
    for a in appts:
        if a.get('appointment_date'):
            a['appointment_date'] = str(a['appointment_date'])
    cur.close(); conn.close()
    return jsonify(appts)


# ─── Transfer Appointments (Transaction + Stored Procedure Demo) ───
@app.route('/appointments/transfer', methods=['POST'])
def transfer_appointments():
    """ALL 3 TECHNIQUES + TRANSACTION:
    1. TECHNIQUE 2 (Input Sanitization): validate doctor IDs
    2. TECHNIQUE 3 (Stored Procedure): sp_transfer_appointments handles all logic
    3. TECHNIQUE 1 (Prepared Statement): %s placeholders for procedure call
    4. TRANSACTION: SERIALIZABLE isolation for full atomicity

    The stored procedure validates both doctors exist, counts appointments,
    and performs the UPDATE — all in one atomic server-side call.
    """
    data = request.json
    try:
        # TECHNIQUE 2: Input Sanitization
        from_doctor_id = sanitize_id(data.get('from_doctor_id'), "Source doctor ID")
        to_doctor_id = sanitize_id(data.get('to_doctor_id'), "Target doctor ID")
    except ValidationError as ve:
        return jsonify({'error': str(ve)}), 400

    if from_doctor_id == to_doctor_id:
        return jsonify({'error': 'Source and target doctor must be different'}), 400

    conn = get_db()
    cur = dict_cursor(conn)
    try:
        # TRANSACTION: SERIALIZABLE isolation for full atomicity
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE)

        # TECHNIQUE 3: Stored Procedure — all logic runs server-side
        # TECHNIQUE 1: Prepared Statement — %s placeholders
        cur.execute(
            "SELECT * FROM sp_transfer_appointments(%s, %s)",
            (from_doctor_id, to_doctor_id)
        )
        result = cur.fetchone()
        conn.commit()
        cur.close(); conn.close()

        return jsonify({
            'message': f'Successfully transferred {result["transferred_count"]} appointment(s) from Dr. {result["from_doctor_name"]} to Dr. {result["to_doctor_name"]}',
            'transferred_count': result['transferred_count'],
            'from_doctor': result['from_doctor_name'],
            'to_doctor': result['to_doctor_name']
        })
    except Exception as e:
        conn.rollback(); cur.close(); conn.close()
        return jsonify({'error': str(e)}), 500


# ─── Dashboard Stats ───────────────────────────────────────────
@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db()
    cur = conn.cursor()
    stats = {}
    for key, query in [
        ('total_patients', "SELECT COUNT(*) FROM patients"),
        ('total_doctors', "SELECT COUNT(*) FROM doctors"),
        ('total_appointments', "SELECT COUNT(*) FROM appointments"),
        ('scheduled_appointments', "SELECT COUNT(*) FROM appointments WHERE status = 'Scheduled'"),
        ('completed_appointments', "SELECT COUNT(*) FROM appointments WHERE status = 'Completed'"),
        ('total_prescriptions', "SELECT COUNT(*) FROM prescriptions"),
        ('departments', "SELECT COUNT(*) FROM departments"),
    ]:
        cur.execute(query)
        stats[key] = cur.fetchone()[0]
    cur.close(); conn.close()
    return jsonify(stats)


# ─── App Entry Point ──────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
