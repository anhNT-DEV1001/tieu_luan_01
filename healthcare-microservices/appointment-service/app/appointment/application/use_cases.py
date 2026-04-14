# appointment/application/use_cases.py
import uuid
from django.utils import timezone
from appointment.domain.entities import Appointment


class BookAppointmentUseCase:
    def __init__(self, appointment_repo, patient_gateway, doctor_gateway):
        self.appointment_repo = appointment_repo
        self.patient_gateway = patient_gateway
        self.doctor_gateway = doctor_gateway

    def execute(self, patient_id, doctor_id, appointment_time):
        if appointment_time <= timezone.now():
            raise ValueError("Appointment time must be in the future")

        if not self.patient_gateway.exists(patient_id):
            raise ValueError("Patient does not exist")

        if not self.doctor_gateway.exists(doctor_id):
            raise ValueError("Doctor does not exist")

        if not self.doctor_gateway.is_available(doctor_id, appointment_time):
            raise ValueError("Doctor is not available")

        if self.appointment_repo.exists_by_doctor_and_time(doctor_id, appointment_time):
            raise ValueError("Doctor already has an appointment at this time")

        appointment = Appointment.create(
            id=uuid.uuid4(),
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_time=appointment_time,
        )

        return self.appointment_repo.save(appointment)


class ListAppointmentsUseCase:
    def __init__(self, appointment_repo):
        self.appointment_repo = appointment_repo

    def execute(self):
        return self.appointment_repo.list()


class GetAppointmentUseCase:
    def __init__(self, appointment_repo):
        self.appointment_repo = appointment_repo

    def execute(self, appointment_id):
        return self.appointment_repo.get(appointment_id)
