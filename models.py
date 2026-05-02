"""
SQLAlchemy ORM Models — Clinic Patient Management System

═══ STAGE 3: ORM (Object Relational Mapping) ═══
ORM maps Python classes to database tables. Instead of writing raw SQL,
we interact with Python objects — SQLAlchemy generates parameterized SQL
internally, which inherently prevents SQL injection.

Example comparison:
  Raw SQL:  cur.execute("SELECT * FROM patients WHERE id = %s", (id,))
  ORM:      session.query(Patient).filter(Patient.id == id).first()

Both are safe from SQL injection, but ORM provides an additional abstraction
layer that makes it harder to accidentally write vulnerable queries.

Reference: SQLInCode_slides.pdf — ORM, Database-Access Approaches
"""

from sqlalchemy import (
    create_engine, Column, Integer, Text, Date, ForeignKey, CheckConstraint
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import os

# ─── Database Connection ──────────────────────────────────────────────────────
DB_USER = 'postgres'
DB_PASS = os.environ.get('PGPASSWORD', 'postgres')
DB_HOST = '127.0.0.1'
DB_PORT = '5432'
DB_NAME = 'clinic_db'

DATABASE_URL = f'postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


# ─── ORM Models ───────────────────────────────────────────────────────────────
# Each class maps to a database table. SQLAlchemy generates all SQL internally
# using parameterized queries — user input never touches raw SQL strings.

class Department(Base):
    """ORM model for the departments table."""
    __tablename__ = 'departments'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    description = Column(Text)

    # Relationship: one department has many doctors
    doctors = relationship('Doctor', back_populates='department')

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'description': self.description}


class Doctor(Base):
    """ORM model for the doctors table."""
    __tablename__ = 'doctors'

    id = Column(Integer, primary_key=True)
    first_name = Column(Text, nullable=False)
    last_name = Column(Text, nullable=False)
    specialization = Column(Text, nullable=False)
    phone = Column(Text)
    email = Column(Text)
    department_id = Column(Integer, ForeignKey('departments.id', ondelete='CASCADE'), nullable=False)

    # Relationships
    department = relationship('Department', back_populates='doctors')
    appointments = relationship('Appointment', back_populates='doctor')

    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'specialization': self.specialization,
            'phone': self.phone,
            'email': self.email,
            'department_id': self.department_id,
            'department_name': self.department.name if self.department else None
        }


class Patient(Base):
    """ORM model for the patients table."""
    __tablename__ = 'patients'

    id = Column(Integer, primary_key=True)
    first_name = Column(Text, nullable=False)
    last_name = Column(Text, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(Text, nullable=False)
    phone = Column(Text)
    email = Column(Text)
    address = Column(Text)

    # Relationship: one patient has many appointments
    appointments = relationship('Appointment', back_populates='patient')

    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'date_of_birth': str(self.date_of_birth) if self.date_of_birth else None,
            'gender': self.gender,
            'phone': self.phone,
            'email': self.email,
            'address': self.address
        }


class Appointment(Base):
    """ORM model for the appointments table."""
    __tablename__ = 'appointments'

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    doctor_id = Column(Integer, ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False)
    appointment_date = Column(Date, nullable=False)
    appointment_time = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default='Scheduled')
    notes = Column(Text)

    # Relationships
    patient = relationship('Patient', back_populates='appointments')
    doctor = relationship('Doctor', back_populates='appointments')
    prescriptions = relationship('Prescription', back_populates='appointment')

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'doctor_id': self.doctor_id,
            'appointment_date': str(self.appointment_date) if self.appointment_date else None,
            'appointment_time': self.appointment_time,
            'status': self.status,
            'notes': self.notes,
            'patient_name': f"{self.patient.first_name} {self.patient.last_name}" if self.patient else None,
            'doctor_name': f"{self.doctor.first_name} {self.doctor.last_name}" if self.doctor else None
        }


class Prescription(Base):
    """ORM model for the prescriptions table."""
    __tablename__ = 'prescriptions'

    id = Column(Integer, primary_key=True)
    appointment_id = Column(Integer, ForeignKey('appointments.id', ondelete='CASCADE'), nullable=False)
    medication = Column(Text, nullable=False)
    dosage = Column(Text, nullable=False)
    duration = Column(Text, nullable=False)
    notes = Column(Text)

    # Relationship
    appointment = relationship('Appointment', back_populates='prescriptions')

    def to_dict(self):
        return {
            'id': self.id,
            'appointment_id': self.appointment_id,
            'medication': self.medication,
            'dosage': self.dosage,
            'duration': self.duration,
            'notes': self.notes,
            'appointment_date': str(self.appointment.appointment_date) if self.appointment else None,
            'patient_name': f"{self.appointment.patient.first_name} {self.appointment.patient.last_name}" if self.appointment and self.appointment.patient else None,
            'doctor_name': f"{self.appointment.doctor.first_name} {self.appointment.doctor.last_name}" if self.appointment and self.appointment.doctor else None
        }


def get_session():
    """Create a new ORM session. Use with `with` or close manually."""
    return SessionLocal()
