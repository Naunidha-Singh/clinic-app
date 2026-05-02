-- CS 348 Project: Clinic Patient Management System
-- Database Schema (PostgreSQL)

-- Departments table
CREATE TABLE IF NOT EXISTS departments (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

-- Doctors table
CREATE TABLE IF NOT EXISTS doctors (
    id SERIAL PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    specialization TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    department_id INTEGER NOT NULL,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE
);

-- Patients table
CREATE TABLE IF NOT EXISTS patients (
    id SERIAL PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    date_of_birth DATE NOT NULL,
    gender TEXT NOT NULL CHECK (gender IN ('Male', 'Female', 'Other')),
    phone TEXT,
    email TEXT,
    address TEXT
);

-- Appointments table
CREATE TABLE IF NOT EXISTS appointments (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Scheduled' CHECK (status IN ('Scheduled', 'Completed', 'Cancelled', 'No Show')),
    notes TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
);

-- Prescriptions table
CREATE TABLE IF NOT EXISTS prescriptions (
    id SERIAL PRIMARY KEY,
    appointment_id INTEGER NOT NULL,
    medication TEXT NOT NULL,
    dosage TEXT NOT NULL,
    duration TEXT NOT NULL,
    notes TEXT,
    FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE
);

-- ═══════════════════════════════════════════════════════════════════════════════
-- INDEXES
-- PostgreSQL supports both B+tree and Hash index types.
-- B+tree: Best for RANGE queries and ORDER BY — leaf nodes form a linked list
--         enabling efficient sequential scans over a range of values.
-- Hash:   Best for POINT (equality) queries — O(1) lookup via hash function,
--         but CANNOT support range queries or ORDER BY.
--
-- We choose the index type based on the query pattern:
--   - Range/ORDER BY queries → B+tree (USING BTREE)
--   - Equality-only queries  → Hash   (USING HASH)
-- ═══════════════════════════════════════════════════════════════════════════════

-- ─── B+tree Indexes (for range queries and ORDER BY) ─────────────────────────

-- Index 1 (B+tree): Patient Report filters patients by date_of_birth for age ranges.
-- This is a RANGE query: WHERE age >= ? AND age <= ? (computed from date_of_birth).
-- B+tree is ideal because the linked list in the leaf nodes allows efficient
-- scanning of all DOB values within the specified range.
-- Query: SELECT ... FROM patients WHERE EXTRACT(YEAR FROM AGE(date_of_birth)) >= ... AND <= ...
-- Used by: Patient Report (Reports page, age range filter)
CREATE INDEX IF NOT EXISTS idx_patients_dob ON patients USING BTREE (date_of_birth);

-- Index 2 (B+tree): Composite index for patient listing and dropdown ORDER BY.
-- B+tree stores entries in sorted order, so this composite index <last_name, first_name>
-- has adjacent data entries matching the ORDER BY clause, avoiding a separate sort step.
-- Query: SELECT ... FROM patients ORDER BY last_name, first_name
-- Used by: Patients page listing, Patient dropdown in Appointment modal
CREATE INDEX IF NOT EXISTS idx_patients_name ON patients USING BTREE (last_name, first_name);

-- Index 3 (B+tree): Appointment Report filters by date RANGE; listing sorted by date.
-- B+tree is ideal for range queries like WHERE date >= ? AND date <= ? because
-- the leaf-level linked list allows sequential scanning of the matching date range.
-- Also benefits ORDER BY appointment_date DESC (reverse scan of B+tree).
-- Query: SELECT ... FROM appointments WHERE appointment_date >= ? AND appointment_date <= ?
-- Used by: Appointment Report (date range filter), Appointments page listing
CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments USING BTREE (appointment_date);

-- ─── Hash Indexes (for point/equality queries) ──────────────────────────────

-- Index 4 (Hash): Patient Report filters by gender (equality: WHERE gender = ?).
-- Hash index provides O(1) lookup for equality checks. B+tree would work but
-- is unnecessarily complex for a pure equality query with low cardinality.
-- Query: SELECT ... FROM patients WHERE gender = ?
-- Used by: Patient Report (Reports page, gender filter)
CREATE INDEX IF NOT EXISTS idx_patients_gender ON patients USING HASH (gender);

-- Index 5 (Hash): Appointment Report filters by status; Dashboard counts by status.
-- Pure equality query: WHERE status = 'Scheduled'. Hash index is optimal.
-- Query: SELECT COUNT(*) FROM appointments WHERE status = 'Scheduled'
-- Used by: Appointment Report (status filter), Dashboard stats (scheduled/completed counts)
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments USING HASH (status);

-- Index 6 (Hash): Appointment Report filters by doctor (equality: WHERE doctor_id = ?).
-- Also supports JOIN operations: appointments JOIN doctors ON doctor_id = id.
-- Query: SELECT ... FROM appointments WHERE doctor_id = ?
-- Used by: Appointment Report (doctor filter), Transfer Appointments feature
CREATE INDEX IF NOT EXISTS idx_appointments_doctor ON appointments USING HASH (doctor_id);

-- Index 7 (Hash): JOIN attribute — appointments.patient_id for equality joins.
-- Query: SELECT ... FROM appointments JOIN patients ON a.patient_id = p.id
-- Used by: Appointments page, Prescriptions page, all appointment-related reports
CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments USING HASH (patient_id);

-- Index 8 (Hash): JOIN attribute — doctors.department_id for equality joins.
-- Query: SELECT ... FROM doctors JOIN departments ON d.department_id = dep.id
-- Used by: Doctors page listing, Doctor dropdown, Appointment Report
CREATE INDEX IF NOT EXISTS idx_doctors_department ON doctors USING HASH (department_id);

-- Index 9 (Hash): JOIN attribute — prescriptions.appointment_id for equality joins.
-- Query: SELECT ... FROM prescriptions JOIN appointments ON pr.appointment_id = a.id
-- Used by: Prescriptions page listing, Prescription dropdown
CREATE INDEX IF NOT EXISTS idx_prescriptions_appointment ON prescriptions USING HASH (appointment_id);

-- ═══════════════════════════════════════════════════════════════════════════════
-- STORED PROCEDURES (PL/pgSQL Functions)
-- Stored procedures encapsulate SQL logic on the database server.
-- Parameters are treated as PL/pgSQL variables — PostgreSQL NEVER interprets
-- them as executable SQL, providing SQL injection protection at the DB level.
--
-- This is a THIRD layer of SQL injection defense (alongside prepared statements
-- and input sanitization in the application layer).
--
-- Reference: SQLInCode_slides.pdf — Stored Procedures, Database-Access Approaches
-- ═══════════════════════════════════════════════════════════════════════════════

-- ─── Stored Procedure 1: Add a new patient ───────────────────────────────────
-- Encapsulates INSERT + RETURNING logic server-side.
-- The application calls: SELECT * FROM sp_add_patient(...)
-- All 7 parameters are bound as PL/pgSQL variables, not interpolated into SQL.
CREATE OR REPLACE FUNCTION sp_add_patient(
    p_first_name TEXT,
    p_last_name TEXT,
    p_dob DATE,
    p_gender TEXT,
    p_phone TEXT DEFAULT '',
    p_email TEXT DEFAULT '',
    p_address TEXT DEFAULT ''
)
RETURNS TABLE (
    id INTEGER,
    first_name TEXT,
    last_name TEXT,
    date_of_birth DATE,
    gender TEXT,
    phone TEXT,
    email TEXT,
    address TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    INSERT INTO patients (first_name, last_name, date_of_birth, gender, phone, email, address)
    VALUES (p_first_name, p_last_name, p_dob, p_gender, p_phone, p_email, p_address)
    RETURNING patients.id, patients.first_name, patients.last_name, patients.date_of_birth,
              patients.gender, patients.phone, patients.email, patients.address;
END;
$$;


-- ─── Stored Procedure 2: Transfer appointments between doctors ───────────────
-- Encapsulates the entire transfer logic: validate both doctors exist,
-- count appointments, perform the UPDATE — all in one atomic server-side call.
-- Uses SERIALIZABLE-equivalent safety because the entire operation runs
-- as a single function call within one transaction.
CREATE OR REPLACE FUNCTION sp_transfer_appointments(
    p_from_doctor_id INTEGER,
    p_to_doctor_id INTEGER
)
RETURNS TABLE (
    transferred_count BIGINT,
    from_doctor_name TEXT,
    to_doctor_name TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_from_name TEXT;
    v_to_name TEXT;
    v_count BIGINT;
BEGIN
    -- Validate source doctor exists
    SELECT first_name || ' ' || last_name INTO v_from_name
    FROM doctors WHERE doctors.id = p_from_doctor_id;
    IF v_from_name IS NULL THEN
        RAISE EXCEPTION 'Source doctor with ID % not found', p_from_doctor_id;
    END IF;

    -- Validate target doctor exists
    SELECT first_name || ' ' || last_name INTO v_to_name
    FROM doctors WHERE doctors.id = p_to_doctor_id;
    IF v_to_name IS NULL THEN
        RAISE EXCEPTION 'Target doctor with ID % not found', p_to_doctor_id;
    END IF;

    -- Count appointments to transfer
    SELECT COUNT(*) INTO v_count
    FROM appointments WHERE doctor_id = p_from_doctor_id;
    IF v_count = 0 THEN
        RAISE EXCEPTION 'Dr. % has no appointments to transfer', v_from_name;
    END IF;

    -- Perform the transfer
    UPDATE appointments SET doctor_id = p_to_doctor_id
    WHERE doctor_id = p_from_doctor_id;

    RETURN QUERY SELECT v_count, v_from_name, v_to_name;
END;
$$;


-- ─── Stored Procedure 3: Patient report with dynamic filters ─────────────────
-- Encapsulates the filtered patient report query server-side.
-- NULL parameters are treated as "no filter" — the COALESCE/conditional logic
-- is handled within the procedure, not by building SQL strings in the app.
CREATE OR REPLACE FUNCTION sp_report_patients(
    p_min_age INTEGER DEFAULT NULL,
    p_max_age INTEGER DEFAULT NULL,
    p_gender TEXT DEFAULT NULL
)
RETURNS TABLE (
    id INTEGER,
    first_name TEXT,
    last_name TEXT,
    date_of_birth DATE,
    gender TEXT,
    phone TEXT,
    email TEXT,
    address TEXT,
    age INTEGER
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT p.id, p.first_name, p.last_name, p.date_of_birth, p.gender,
           p.phone, p.email, p.address,
           EXTRACT(YEAR FROM AGE(p.date_of_birth))::INTEGER as age
    FROM patients p
    WHERE (p_min_age IS NULL OR EXTRACT(YEAR FROM AGE(p.date_of_birth)) >= p_min_age)
      AND (p_max_age IS NULL OR EXTRACT(YEAR FROM AGE(p.date_of_birth)) <= p_max_age)
      AND (p_gender IS NULL OR p.gender = p_gender)
    ORDER BY p.last_name, p.first_name;
END;
$$;
