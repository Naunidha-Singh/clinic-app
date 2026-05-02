-- Seed Data for Clinic Patient Management System (PostgreSQL)

-- Departments
INSERT INTO departments (name, description) VALUES
('Cardiology', 'Heart and cardiovascular system'),
('Neurology', 'Brain and nervous system disorders'),
('Orthopedics', 'Bones, joints, and musculoskeletal system'),
('Pediatrics', 'Medical care for infants, children, and adolescents'),
('Dermatology', 'Skin, hair, and nail conditions'),
('General Medicine', 'Primary care and general health');

-- Doctors
INSERT INTO doctors (first_name, last_name, specialization, phone, email, department_id) VALUES
('Sarah', 'Johnson', 'Interventional Cardiology', '555-0101', 'sarah.johnson@clinic.com', 1),
('Michael', 'Chen', 'Electrophysiology', '555-0102', 'michael.chen@clinic.com', 1),
('Emily', 'Williams', 'Neurophysiology', '555-0103', 'emily.williams@clinic.com', 2),
('James', 'Brown', 'Spine Surgery', '555-0104', 'james.brown@clinic.com', 3),
('Maria', 'Garcia', 'Sports Medicine', '555-0105', 'maria.garcia@clinic.com', 3),
('David', 'Kim', 'Neonatal Care', '555-0106', 'david.kim@clinic.com', 4),
('Lisa', 'Anderson', 'Clinical Dermatology', '555-0107', 'lisa.anderson@clinic.com', 5),
('Robert', 'Taylor', 'Internal Medicine', '555-0108', 'robert.taylor@clinic.com', 6);

-- Patients
INSERT INTO patients (first_name, last_name, date_of_birth, gender, phone, email, address) VALUES
('John', 'Smith', '1985-03-15', 'Male', '555-1001', 'john.smith@email.com', '123 Oak Street, Springfield'),
('Emma', 'Davis', '1990-07-22', 'Female', '555-1002', 'emma.davis@email.com', '456 Maple Ave, Springfield'),
('William', 'Martinez', '1978-11-08', 'Male', '555-1003', 'william.martinez@email.com', '789 Pine Road, Shelbyville'),
('Olivia', 'Wilson', '2001-01-30', 'Female', '555-1004', 'olivia.wilson@email.com', '321 Elm Street, Springfield'),
('James', 'Taylor', '1965-09-12', 'Male', '555-1005', 'james.t@email.com', '654 Cedar Lane, Capital City'),
('Sophia', 'Anderson', '1995-04-18', 'Female', '555-1006', 'sophia.a@email.com', '987 Birch Drive, Shelbyville'),
('Benjamin', 'Thomas', '1958-12-25', 'Male', '555-1007', 'ben.thomas@email.com', '147 Walnut Court, Springfield'),
('Isabella', 'Jackson', '2005-06-14', 'Female', '555-1008', 'isabella.j@email.com', '258 Ash Boulevard, Capital City'),
('Alexander', 'White', '1972-08-03', 'Male', '555-1009', 'alex.white@email.com', '369 Spruce Way, Springfield'),
('Mia', 'Harris', '1988-02-27', 'Female', '555-1010', 'mia.harris@email.com', '741 Poplar Street, Shelbyville'),
('Ethan', 'Clark', '2010-10-05', 'Male', '555-1011', 'ethan.clark@email.com', '852 Willow Lane, Springfield'),
('Charlotte', 'Lewis', '1993-05-20', 'Female', '555-1012', 'charlotte.l@email.com', '963 Cypress Road, Capital City'),
('Daniel', 'Robinson', '1980-07-16', 'Male', '555-1013', 'daniel.r@email.com', '159 Hickory Ave, Springfield'),
('Amelia', 'Walker', '1999-11-11', 'Female', '555-1014', 'amelia.w@email.com', '357 Magnolia Drive, Shelbyville'),
('Henry', 'Young', '1955-03-28', 'Male', '555-1015', 'henry.young@email.com', '468 Redwood Court, Capital City');

-- Appointments
INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, status, notes) VALUES
(1, 1, '2026-03-15', '09:00', 'Completed', 'Routine cardiac checkup'),
(2, 3, '2026-03-16', '10:30', 'Completed', 'Headache and dizziness evaluation'),
(3, 4, '2026-03-17', '14:00', 'Completed', 'Lower back pain consultation'),
(4, 7, '2026-03-18', '11:00', 'Completed', 'Skin rash examination'),
(5, 1, '2026-03-19', '08:30', 'Completed', 'Follow-up after heart procedure'),
(6, 5, '2026-03-20', '15:30', 'Completed', 'Knee injury assessment'),
(7, 8, '2026-03-21', '09:00', 'Completed', 'Annual physical exam'),
(8, 6, '2026-03-22', '10:00', 'Cancelled', 'Pediatric wellness check'),
(9, 2, '2026-03-25', '13:00', 'Completed', 'Heart rhythm evaluation'),
(10, 3, '2026-03-26', '14:30', 'Completed', 'Migraine follow-up'),
(1, 8, '2026-04-01', '09:00', 'Scheduled', 'General checkup'),
(3, 4, '2026-04-02', '11:00', 'Scheduled', 'Spine follow-up'),
(5, 1, '2026-04-03', '10:00', 'Scheduled', 'Cardiac stress test'),
(11, 6, '2026-04-04', '14:00', 'Scheduled', 'Child wellness visit'),
(12, 7, '2026-04-05', '09:30', 'Scheduled', 'Skin biopsy results discussion'),
(13, 5, '2026-04-07', '15:00', 'Scheduled', 'Joint pain evaluation'),
(14, 3, '2026-04-08', '10:00', 'Scheduled', 'Neurological assessment'),
(15, 8, '2026-04-09', '11:00', 'Scheduled', 'Senior health screening'),
(2, 1, '2026-04-10', '08:30', 'Scheduled', 'Cardiac screening'),
(6, 4, '2026-04-11', '13:00', 'Scheduled', 'Orthopedic follow-up');

-- Prescriptions
INSERT INTO prescriptions (appointment_id, medication, dosage, duration, notes) VALUES
(1, 'Lisinopril', '10mg daily', '30 days', 'Monitor blood pressure weekly'),
(1, 'Aspirin', '81mg daily', '90 days', 'Low-dose for heart health'),
(2, 'Sumatriptan', '50mg as needed', '30 days', 'For acute migraine episodes'),
(3, 'Ibuprofen', '400mg three times daily', '14 days', 'Take with food'),
(3, 'Cyclobenzaprine', '10mg at bedtime', '10 days', 'Muscle relaxant for back spasm'),
(4, 'Hydrocortisone Cream', 'Apply twice daily', '14 days', 'Apply to affected areas only'),
(5, 'Metoprolol', '25mg twice daily', '30 days', 'Beta-blocker post procedure'),
(6, 'Naproxen', '500mg twice daily', '14 days', 'Anti-inflammatory for knee'),
(7, 'Vitamin D3', '2000 IU daily', '90 days', 'Supplement for deficiency'),
(9, 'Flecainide', '100mg twice daily', '30 days', 'Antiarrhythmic medication'),
(10, 'Topiramate', '25mg daily', '30 days', 'Migraine prevention; increase to 50mg after 2 weeks');
