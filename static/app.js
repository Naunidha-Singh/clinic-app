/* ═══════════════════════════════════════════════════════════
   CS 348 Project — ClinicPro Frontend Application Logic
   ═══════════════════════════════════════════════════════════ */

// ─── Navigation ──────────────────────────────────────────────

document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const page = link.dataset.page;
        switchPage(page);
    });
});

function switchPage(pageName) {
    // Update nav
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    document.querySelector(`[data-page="${pageName}"]`).classList.add('active');

    // Update pages
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(`page-${pageName}`).classList.add('active');

    // Load data for the page
    loadPageData(pageName);
}

function loadPageData(pageName) {
    switch (pageName) {
        case 'dashboard': loadDashboard(); break;
        case 'patients': loadPatients(); break;
        case 'doctors': loadDoctors(); loadTransferDropdowns(); break;
        case 'appointments': loadAppointments(); break;
        case 'prescriptions': loadPrescriptions(); break;
        case 'reports': loadReportDropdowns(); break;
    }
}

// ─── Toast ───────────────────────────────────────────────────

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} active`;
    setTimeout(() => { toast.classList.remove('active'); }, 3000);
}

// ─── Dashboard ───────────────────────────────────────────────

async function loadDashboard() {
    try {
        const res = await fetch('/api/stats');
        const stats = await res.json();
        document.getElementById('stat-patients').textContent = stats.total_patients;
        document.getElementById('stat-doctors').textContent = stats.total_doctors;
        document.getElementById('stat-appointments').textContent = stats.total_appointments;
        document.getElementById('stat-scheduled').textContent = stats.scheduled_appointments;
        document.getElementById('stat-completed').textContent = stats.completed_appointments;
        document.getElementById('stat-prescriptions').textContent = stats.total_prescriptions;
    } catch (err) {
        console.error('Failed to load stats:', err);
    }
}

// ─── Modal Helpers ───────────────────────────────────────────

function openModal(modalId) {
    document.getElementById('modal-overlay').classList.add('active');
    document.getElementById(modalId).classList.add('active');
}

function closeModal() {
    document.getElementById('modal-overlay').classList.remove('active');
    document.querySelectorAll('.modal').forEach(m => m.classList.remove('active'));
}

// ─── PATIENTS ────────────────────────────────────────────────

async function loadPatients() {
    try {
        const res = await fetch('/patients');
        const patients = await res.json();
        const tbody = document.getElementById('patients-tbody');
        if (patients.length === 0) {
            tbody.innerHTML = '<tr class="empty-row"><td colspan="7">No patients found</td></tr>';
            return;
        }
        tbody.innerHTML = patients.map(p => `
            <tr>
                <td>${p.id}</td>
                <td>${p.first_name} ${p.last_name}</td>
                <td>${p.date_of_birth}</td>
                <td>${p.gender}</td>
                <td>${p.phone || '—'}</td>
                <td>${p.email || '—'}</td>
                <td>
                    <div class="action-buttons">
                        <button class="btn btn-sm btn-edit" onclick='editPatient(${JSON.stringify(p)})'>Edit</button>
                        <button class="btn btn-sm btn-danger" onclick="deletePatient(${p.id})">Delete</button>
                    </div>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Failed to load patients:', err);
    }
}

function openPatientModal() {
    document.getElementById('patient-modal-title').textContent = 'Add Patient';
    document.getElementById('patient-form').reset();
    document.getElementById('patient-id').value = '';
    openModal('patient-modal');
}

function editPatient(patient) {
    document.getElementById('patient-modal-title').textContent = 'Edit Patient';
    document.getElementById('patient-id').value = patient.id;
    document.getElementById('patient-first-name').value = patient.first_name;
    document.getElementById('patient-last-name').value = patient.last_name;
    document.getElementById('patient-dob').value = patient.date_of_birth;
    document.getElementById('patient-gender').value = patient.gender;
    document.getElementById('patient-phone').value = patient.phone || '';
    document.getElementById('patient-email').value = patient.email || '';
    document.getElementById('patient-address').value = patient.address || '';
    openModal('patient-modal');
}

async function savePatient(e) {
    e.preventDefault();
    const id = document.getElementById('patient-id').value;
    const data = {
        first_name: document.getElementById('patient-first-name').value,
        last_name: document.getElementById('patient-last-name').value,
        date_of_birth: document.getElementById('patient-dob').value,
        gender: document.getElementById('patient-gender').value,
        phone: document.getElementById('patient-phone').value,
        email: document.getElementById('patient-email').value,
        address: document.getElementById('patient-address').value,
    };

    try {
        const url = id ? `/patients/${id}` : '/patients';
        const method = id ? 'PUT' : 'POST';
        const res = await fetch(url, {
            method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error('Failed to save');
        closeModal();
        showToast(id ? 'Patient updated successfully' : 'Patient added successfully');
        loadPatients();
    } catch (err) {
        showToast('Error saving patient', 'error');
    }
}

async function deletePatient(id) {
    if (!confirm('Are you sure you want to delete this patient? This will also delete their appointments.')) return;
    try {
        const res = await fetch(`/patients/${id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('Failed to delete');
        showToast('Patient deleted successfully');
        loadPatients();
    } catch (err) {
        showToast('Error deleting patient', 'error');
    }
}

// ─── DOCTORS ─────────────────────────────────────────────────

async function loadDoctors() {
    try {
        const res = await fetch('/doctors');
        const doctors = await res.json();
        const tbody = document.getElementById('doctors-tbody');
        if (doctors.length === 0) {
            tbody.innerHTML = '<tr class="empty-row"><td colspan="7">No doctors found</td></tr>';
            return;
        }
        tbody.innerHTML = doctors.map(d => `
            <tr>
                <td>${d.id}</td>
                <td>Dr. ${d.first_name} ${d.last_name}</td>
                <td>${d.specialization}</td>
                <td>${d.department_name}</td>
                <td>${d.phone || '—'}</td>
                <td>${d.email || '—'}</td>
                <td>
                    <div class="action-buttons">
                        <button class="btn btn-sm btn-edit" onclick='editDoctor(${JSON.stringify(d)})'>Edit</button>
                        <button class="btn btn-sm btn-danger" onclick="deleteDoctor(${d.id})">Delete</button>
                    </div>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Failed to load doctors:', err);
    }
}

async function openDoctorModal() {
    document.getElementById('doctor-modal-title').textContent = 'Add Doctor';
    document.getElementById('doctor-form').reset();
    document.getElementById('doctor-id').value = '';
    await loadDepartmentDropdown('doctor-department');
    openModal('doctor-modal');
}

async function editDoctor(doctor) {
    document.getElementById('doctor-modal-title').textContent = 'Edit Doctor';
    document.getElementById('doctor-id').value = doctor.id;
    document.getElementById('doctor-first-name').value = doctor.first_name;
    document.getElementById('doctor-last-name').value = doctor.last_name;
    document.getElementById('doctor-specialization').value = doctor.specialization;
    document.getElementById('doctor-phone').value = doctor.phone || '';
    document.getElementById('doctor-email').value = doctor.email || '';
    await loadDepartmentDropdown('doctor-department');
    document.getElementById('doctor-department').value = doctor.department_id;
    openModal('doctor-modal');
}

async function saveDoctor(e) {
    e.preventDefault();
    const id = document.getElementById('doctor-id').value;
    const data = {
        first_name: document.getElementById('doctor-first-name').value,
        last_name: document.getElementById('doctor-last-name').value,
        specialization: document.getElementById('doctor-specialization').value,
        department_id: document.getElementById('doctor-department').value,
        phone: document.getElementById('doctor-phone').value,
        email: document.getElementById('doctor-email').value,
    };

    try {
        const url = id ? `/doctors/${id}` : '/doctors';
        const method = id ? 'PUT' : 'POST';
        const res = await fetch(url, {
            method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error('Failed to save');
        closeModal();
        showToast(id ? 'Doctor updated successfully' : 'Doctor added successfully');
        loadDoctors();
    } catch (err) {
        showToast('Error saving doctor', 'error');
    }
}

async function deleteDoctor(id) {
    if (!confirm('Are you sure you want to delete this doctor?')) return;
    try {
        const res = await fetch(`/doctors/${id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('Failed to delete');
        showToast('Doctor deleted successfully');
        loadDoctors();
    } catch (err) {
        showToast('Error deleting doctor', 'error');
    }
}

// ─── TRANSFER APPOINTMENTS (Transaction Demo) ───────────────

async function loadTransferDropdowns() {
    await Promise.all([
        loadDoctorDropdown('transfer-from-doctor'),
        loadDoctorDropdown('transfer-to-doctor')
    ]);
}

async function transferAppointments() {
    const fromId = document.getElementById('transfer-from-doctor').value;
    const toId = document.getElementById('transfer-to-doctor').value;

    if (!fromId || !toId) {
        showToast('Please select both source and target doctors', 'error');
        return;
    }

    if (fromId === toId) {
        showToast('Source and target doctor must be different', 'error');
        return;
    }

    if (!confirm('Transfer ALL appointments from the selected source doctor to the target doctor? This uses a database transaction to ensure atomicity.')) return;

    try {
        const res = await fetch('/appointments/transfer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ from_doctor_id: fromId, to_doctor_id: toId })
        });
        const result = await res.json();
        const resultDiv = document.getElementById('transfer-result');

        if (!res.ok) {
            resultDiv.textContent = `❌ ${result.error}`;
            resultDiv.className = 'report-summary visible';
            showToast(result.error, 'error');
            return;
        }

        resultDiv.textContent = `✅ ${result.message}`;
        resultDiv.className = 'report-summary visible';
        showToast(result.message);
        loadDoctors();
    } catch (err) {
        showToast('Error transferring appointments', 'error');
    }
}

// ─── APPOINTMENTS ────────────────────────────────────────────

async function loadAppointments() {
    try {
        const res = await fetch('/appointments');
        const appts = await res.json();
        const tbody = document.getElementById('appointments-tbody');
        if (appts.length === 0) {
            tbody.innerHTML = '<tr class="empty-row"><td colspan="7">No appointments found</td></tr>';
            return;
        }
        tbody.innerHTML = appts.map(a => `
            <tr>
                <td>${a.id}</td>
                <td>${a.patient_name}</td>
                <td>Dr. ${a.doctor_name}</td>
                <td>${a.appointment_date}</td>
                <td>${a.appointment_time}</td>
                <td><span class="badge badge-${a.status.toLowerCase().replace(' ', '')}">${a.status}</span></td>
                <td>
                    <div class="action-buttons">
                        <button class="btn btn-sm btn-edit" onclick='editAppointment(${JSON.stringify(a)})'>Edit</button>
                        <button class="btn btn-sm btn-danger" onclick="deleteAppointment(${a.id})">Delete</button>
                    </div>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Failed to load appointments:', err);
    }
}

async function openAppointmentModal() {
    document.getElementById('appointment-modal-title').textContent = 'New Appointment';
    document.getElementById('appointment-form').reset();
    document.getElementById('appointment-id').value = '';
    // Populate dropdowns dynamically from DB
    await Promise.all([
        loadPatientDropdown('appointment-patient'),
        loadDoctorDropdown('appointment-doctor')
    ]);
    openModal('appointment-modal');
}

async function editAppointment(appt) {
    document.getElementById('appointment-modal-title').textContent = 'Edit Appointment';
    document.getElementById('appointment-id').value = appt.id;
    document.getElementById('appointment-date').value = appt.appointment_date;
    document.getElementById('appointment-time').value = appt.appointment_time;
    document.getElementById('appointment-status').value = appt.status;
    document.getElementById('appointment-notes').value = appt.notes || '';
    await Promise.all([
        loadPatientDropdown('appointment-patient'),
        loadDoctorDropdown('appointment-doctor')
    ]);
    document.getElementById('appointment-patient').value = appt.patient_id;
    document.getElementById('appointment-doctor').value = appt.doctor_id;
    openModal('appointment-modal');
}

async function saveAppointment(e) {
    e.preventDefault();
    const id = document.getElementById('appointment-id').value;
    const data = {
        patient_id: document.getElementById('appointment-patient').value,
        doctor_id: document.getElementById('appointment-doctor').value,
        appointment_date: document.getElementById('appointment-date').value,
        appointment_time: document.getElementById('appointment-time').value,
        status: document.getElementById('appointment-status').value,
        notes: document.getElementById('appointment-notes').value,
    };

    try {
        const url = id ? `/appointments/${id}` : '/appointments';
        const method = id ? 'PUT' : 'POST';
        const res = await fetch(url, {
            method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error('Failed to save');
        closeModal();
        showToast(id ? 'Appointment updated successfully' : 'Appointment created successfully');
        loadAppointments();
    } catch (err) {
        showToast('Error saving appointment', 'error');
    }
}

async function deleteAppointment(id) {
    if (!confirm('Are you sure you want to delete this appointment?')) return;
    try {
        const res = await fetch(`/appointments/${id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('Failed to delete');
        showToast('Appointment deleted successfully');
        loadAppointments();
    } catch (err) {
        showToast('Error deleting appointment', 'error');
    }
}

// ─── PRESCRIPTIONS ───────────────────────────────────────────

async function loadPrescriptions() {
    try {
        const res = await fetch('/prescriptions');
        const prescriptions = await res.json();
        const tbody = document.getElementById('prescriptions-tbody');
        if (prescriptions.length === 0) {
            tbody.innerHTML = '<tr class="empty-row"><td colspan="8">No prescriptions found</td></tr>';
            return;
        }
        tbody.innerHTML = prescriptions.map(pr => `
            <tr>
                <td>${pr.id}</td>
                <td>${pr.patient_name}</td>
                <td>Dr. ${pr.doctor_name}</td>
                <td>${pr.appointment_date}</td>
                <td>${pr.medication}</td>
                <td>${pr.dosage}</td>
                <td>${pr.duration}</td>
                <td>
                    <div class="action-buttons">
                        <button class="btn btn-sm btn-edit" onclick='editPrescription(${JSON.stringify(pr)})'>Edit</button>
                        <button class="btn btn-sm btn-danger" onclick="deletePrescription(${pr.id})">Delete</button>
                    </div>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Failed to load prescriptions:', err);
    }
}

async function openPrescriptionModal() {
    document.getElementById('prescription-modal-title').textContent = 'New Prescription';
    document.getElementById('prescription-form').reset();
    document.getElementById('prescription-id').value = '';
    await loadAppointmentDropdown('prescription-appointment');
    openModal('prescription-modal');
}

async function editPrescription(presc) {
    document.getElementById('prescription-modal-title').textContent = 'Edit Prescription';
    document.getElementById('prescription-id').value = presc.id;
    document.getElementById('prescription-medication').value = presc.medication;
    document.getElementById('prescription-dosage').value = presc.dosage;
    document.getElementById('prescription-duration').value = presc.duration;
    document.getElementById('prescription-notes').value = presc.notes || '';
    await loadAppointmentDropdown('prescription-appointment');
    document.getElementById('prescription-appointment').value = presc.appointment_id;
    openModal('prescription-modal');
}

async function savePrescription(e) {
    e.preventDefault();
    const id = document.getElementById('prescription-id').value;
    const data = {
        appointment_id: document.getElementById('prescription-appointment').value,
        medication: document.getElementById('prescription-medication').value,
        dosage: document.getElementById('prescription-dosage').value,
        duration: document.getElementById('prescription-duration').value,
        notes: document.getElementById('prescription-notes').value,
    };

    try {
        const url = id ? `/prescriptions/${id}` : '/prescriptions';
        const method = id ? 'PUT' : 'POST';
        const res = await fetch(url, {
            method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error('Failed to save');
        closeModal();
        showToast(id ? 'Prescription updated successfully' : 'Prescription created successfully');
        loadPrescriptions();
    } catch (err) {
        showToast('Error saving prescription', 'error');
    }
}

async function deletePrescription(id) {
    if (!confirm('Are you sure you want to delete this prescription?')) return;
    try {
        const res = await fetch(`/prescriptions/${id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('Failed to delete');
        showToast('Prescription deleted successfully');
        loadPrescriptions();
    } catch (err) {
        showToast('Error deleting prescription', 'error');
    }
}

// ─── Dynamic Dropdown Loaders (from DB) ──────────────────────

async function loadDepartmentDropdown(selectId) {
    const res = await fetch('/api/departments');
    const departments = await res.json();
    const select = document.getElementById(selectId);
    const currentVal = select.value;
    select.innerHTML = '<option value="">Select Department...</option>' +
        departments.map(d => `<option value="${d.id}">${d.name}</option>`).join('');
    if (currentVal) select.value = currentVal;
}

async function loadDoctorDropdown(selectId) {
    const res = await fetch('/api/doctors');
    const doctors = await res.json();
    const select = document.getElementById(selectId);
    const currentVal = select.value;
    select.innerHTML = '<option value="">Select Doctor...</option>' +
        doctors.map(d => `<option value="${d.id}">Dr. ${d.name} — ${d.specialization}</option>`).join('');
    if (currentVal) select.value = currentVal;
}

async function loadPatientDropdown(selectId) {
    const res = await fetch('/api/patients');
    const patients = await res.json();
    const select = document.getElementById(selectId);
    const currentVal = select.value;
    select.innerHTML = '<option value="">Select Patient...</option>' +
        patients.map(p => `<option value="${p.id}">${p.name}</option>`).join('');
    if (currentVal) select.value = currentVal;
}

async function loadAppointmentDropdown(selectId) {
    const res = await fetch('/api/appointments');
    const appts = await res.json();
    const select = document.getElementById(selectId);
    const currentVal = select.value;
    select.innerHTML = '<option value="">Select Appointment...</option>' +
        appts.map(a => `<option value="${a.id}">${a.label}</option>`).join('');
    if (currentVal) select.value = currentVal;
}

// ─── Report Tabs ─────────────────────────────────────────────

function switchReportTab(tab) {
    document.querySelectorAll('.report-tab').forEach(t => t.classList.remove('active'));
    document.getElementById(`tab-${tab}-report`).classList.add('active');

    if (tab === 'patient') {
        document.getElementById('filter-patient-report').classList.remove('hidden');
        document.getElementById('filter-appointment-report').classList.add('hidden');
    } else {
        document.getElementById('filter-patient-report').classList.add('hidden');
        document.getElementById('filter-appointment-report').classList.remove('hidden');
    }
}

async function loadReportDropdowns() {
    // Load doctor dropdown for appointment report filter
    await loadDoctorDropdown('filter-doctor');
}

// ─── Patient Report ──────────────────────────────────────────

async function runPatientReport() {
    const minAge = document.getElementById('filter-min-age').value;
    const maxAge = document.getElementById('filter-max-age').value;
    const gender = document.getElementById('filter-gender').value;

    let url = '/reports/patients?';
    if (minAge) url += `min_age=${minAge}&`;
    if (maxAge) url += `max_age=${maxAge}&`;
    if (gender) url += `gender=${gender}&`;

    try {
        const res = await fetch(url);
        const patients = await res.json();
        const tbody = document.getElementById('patient-report-tbody');
        const summary = document.getElementById('patient-report-summary');

        // Build filter description
        let filterDesc = [];
        if (minAge || maxAge) filterDesc.push(`Age: ${minAge || '0'}–${maxAge || '∞'}`);
        if (gender) filterDesc.push(`Gender: ${gender}`);
        const filterStr = filterDesc.length > 0 ? ` | Filters: ${filterDesc.join(', ')}` : ' | No filters applied';

        summary.textContent = `📋 Report: ${patients.length} patient(s) found${filterStr}`;
        summary.classList.add('visible');

        if (patients.length === 0) {
            tbody.innerHTML = '<tr class="empty-row"><td colspan="7">No patients match the criteria</td></tr>';
            return;
        }

        tbody.innerHTML = patients.map(p => `
            <tr>
                <td>${p.id}</td>
                <td>${p.first_name} ${p.last_name}</td>
                <td>${p.age}</td>
                <td>${p.gender}</td>
                <td>${p.phone || '—'}</td>
                <td>${p.email || '—'}</td>
                <td>${p.address || '—'}</td>
            </tr>
        `).join('');
    } catch (err) {
        showToast('Error generating report', 'error');
    }
}

function clearPatientFilters() {
    document.getElementById('filter-min-age').value = '';
    document.getElementById('filter-max-age').value = '';
    document.getElementById('filter-gender').value = '';
    document.getElementById('patient-report-summary').classList.remove('visible');
    document.getElementById('patient-report-tbody').innerHTML = '';
}

// ─── Appointment Report ──────────────────────────────────────

async function runAppointmentReport() {
    const startDate = document.getElementById('filter-start-date').value;
    const endDate = document.getElementById('filter-end-date').value;
    const doctorId = document.getElementById('filter-doctor').value;
    const status = document.getElementById('filter-status').value;

    let url = '/reports/appointments?';
    if (startDate) url += `start_date=${startDate}&`;
    if (endDate) url += `end_date=${endDate}&`;
    if (doctorId) url += `doctor_id=${doctorId}&`;
    if (status) url += `status=${status}&`;

    try {
        const res = await fetch(url);
        const appts = await res.json();
        const tbody = document.getElementById('appointment-report-tbody');
        const summary = document.getElementById('appointment-report-summary');

        let filterDesc = [];
        if (startDate || endDate) filterDesc.push(`Date: ${startDate || '∞'}–${endDate || '∞'}`);
        if (doctorId) {
            const docSelect = document.getElementById('filter-doctor');
            filterDesc.push(`Doctor: ${docSelect.options[docSelect.selectedIndex].text}`);
        }
        if (status) filterDesc.push(`Status: ${status}`);
        const filterStr = filterDesc.length > 0 ? ` | Filters: ${filterDesc.join(', ')}` : ' | No filters applied';

        summary.textContent = `📋 Report: ${appts.length} appointment(s) found${filterStr}`;
        summary.classList.add('visible');

        if (appts.length === 0) {
            tbody.innerHTML = '<tr class="empty-row"><td colspan="8">No appointments match the criteria</td></tr>';
            return;
        }

        tbody.innerHTML = appts.map(a => `
            <tr>
                <td>${a.id}</td>
                <td>${a.patient_name}</td>
                <td>Dr. ${a.doctor_name}</td>
                <td>${a.department}</td>
                <td>${a.appointment_date}</td>
                <td>${a.appointment_time}</td>
                <td><span class="badge badge-${a.status.toLowerCase().replace(' ', '')}">${a.status}</span></td>
                <td>${a.notes || '—'}</td>
            </tr>
        `).join('');
    } catch (err) {
        showToast('Error generating report', 'error');
    }
}

function clearAppointmentFilters() {
    document.getElementById('filter-start-date').value = '';
    document.getElementById('filter-end-date').value = '';
    document.getElementById('filter-doctor').value = '';
    document.getElementById('filter-status').value = '';
    document.getElementById('appointment-report-summary').classList.remove('visible');
    document.getElementById('appointment-report-tbody').innerHTML = '';
}

// ─── Initial Load ────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
});
