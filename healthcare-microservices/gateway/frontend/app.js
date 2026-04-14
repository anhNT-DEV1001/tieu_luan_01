const state = {
  patients: [],
  doctors: [],
  appointments: [],
};

const elements = {
  patientsList: document.getElementById("patients-list"),
  doctorsList: document.getElementById("doctors-list"),
  appointmentsList: document.getElementById("appointments-list"),
  patientsEmpty: document.getElementById("patients-empty"),
  doctorsEmpty: document.getElementById("doctors-empty"),
  appointmentsEmpty: document.getElementById("appointments-empty"),
  patientSelect: document.getElementById("patient-select"),
  doctorSelect: document.getElementById("doctor-select"),
  patientForm: document.getElementById("patient-form"),
  doctorForm: document.getElementById("doctor-form"),
  appointmentForm: document.getElementById("appointment-form"),
  messageLog: document.getElementById("message-log"),
};

function logMessage(message, type = "info") {
  const item = document.createElement("div");
  item.className = `message-item ${type === "error" ? "error" : ""}`.trim();
  item.innerHTML = `
    <span class="message-time">${new Date().toLocaleString()}</span>
    <strong>${type === "error" ? "Error" : "Update"}</strong>
    <div>${message}</div>
  `;
  elements.messageLog.prepend(item);
}

async function apiRequest(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${response.status}`);
  }

  return response.json();
}

function renderEntityList(items, container, emptyNode, formatter) {
  container.innerHTML = "";
  emptyNode.style.display = items.length ? "none" : "block";

  items.forEach((item) => {
    const card = document.createElement("article");
    card.className = "entity-card";
    card.innerHTML = formatter(item);
    container.appendChild(card);
  });
}

function renderPatients() {
  renderEntityList(state.patients, elements.patientsList, elements.patientsEmpty, (patient) => `
    <strong>${patient.full_name}</strong>
    <div class="meta">Phone: ${patient.phone}</div>
    <div class="meta">ID: ${patient.id}</div>
  `);

  elements.patientSelect.innerHTML = state.patients.length
    ? state.patients.map((patient) => `<option value="${patient.id}">${patient.full_name}</option>`).join("")
    : '<option value="">Chua co patient</option>';
}

function renderDoctors() {
  renderEntityList(state.doctors, elements.doctorsList, elements.doctorsEmpty, (doctor) => `
    <strong>${doctor.full_name}</strong>
    <div class="meta">Specialty: ${doctor.specialty}</div>
    <div class="meta">ID: ${doctor.id}</div>
  `);

  elements.doctorSelect.innerHTML = state.doctors.length
    ? state.doctors.map((doctor) => `<option value="${doctor.id}">${doctor.full_name} - ${doctor.specialty}</option>`).join("")
    : '<option value="">Chua co doctor</option>';
}

function findNameById(collection, id, fallback) {
  return collection.find((item) => item.id === id)?.full_name || fallback;
}

function renderAppointments() {
  elements.appointmentsList.innerHTML = "";
  elements.appointmentsEmpty.style.display = state.appointments.length ? "none" : "block";

  state.appointments.forEach((appointment) => {
    const item = document.createElement("article");
    item.className = "timeline-item";
    item.innerHTML = `
      <div class="status-pill">${appointment.status}</div>
      <strong>${findNameById(state.patients, appointment.patient_id, appointment.patient_id)}</strong>
      <div class="meta">Doctor: ${findNameById(state.doctors, appointment.doctor_id, appointment.doctor_id)}</div>
      <div class="meta">Time: ${new Date(appointment.appointment_time).toLocaleString()}</div>
      <div class="meta">Appointment ID: ${appointment.id}</div>
    `;
    elements.appointmentsList.appendChild(item);
  });
}

async function loadPatients() {
  state.patients = await apiRequest("/api/patients/");
  renderPatients();
}

async function loadDoctors() {
  state.doctors = await apiRequest("/api/doctors/");
  renderDoctors();
}

async function loadAppointments() {
  state.appointments = await apiRequest("/api/appointments/");
  renderAppointments();
}

function toUtcISOString(datetimeLocalValue) {
  return new Date(datetimeLocalValue).toISOString();
}

function setDefaultAppointmentTime() {
  document.getElementById("appointment-time").value = new Date(Date.now() + 86400000)
    .toISOString()
    .slice(0, 16);
}

async function initializeDashboard() {
  await Promise.all([loadPatients(), loadDoctors(), loadAppointments()]);
  logMessage("Dashboard synced with gateway.");
}

elements.patientForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);
  const payload = Object.fromEntries(formData.entries());

  try {
    const patient = await apiRequest("/api/patients/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    form.reset();
    await loadPatients();
    logMessage(`Created patient ${patient.full_name}.`);
  } catch (error) {
    logMessage(error.message, "error");
  }
});

elements.doctorForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);
  const payload = Object.fromEntries(formData.entries());

  try {
    const doctor = await apiRequest("/api/doctors/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    form.reset();
    await loadDoctors();
    logMessage(`Created doctor ${doctor.full_name}.`);
  } catch (error) {
    logMessage(error.message, "error");
  }
});

elements.appointmentForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);
  const payload = Object.fromEntries(formData.entries());
  payload.appointment_time = toUtcISOString(payload.appointment_time);

  try {
    const appointment = await apiRequest("/api/appointments/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    form.reset();
    setDefaultAppointmentTime();
    await Promise.all([loadPatients(), loadDoctors(), loadAppointments()]);
    logMessage(`Booked appointment ${appointment.id}.`);
  } catch (error) {
    logMessage(error.message, "error");
  }
});

document.getElementById("refresh-patients").addEventListener("click", () => loadPatients());
document.getElementById("refresh-doctors").addEventListener("click", () => loadDoctors());
document.getElementById("refresh-appointments").addEventListener("click", () => loadAppointments());
document.getElementById("clear-log").addEventListener("click", () => {
  elements.messageLog.innerHTML = "";
});

setDefaultAppointmentTime();

initializeDashboard().catch((error) => logMessage(error.message, "error"));
