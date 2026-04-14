# appointment/infrastructure/repositories.py
from appointment.infrastructure.models import AppointmentModel
from appointment.domain.entities import Appointment


class DjangoAppointmentRepository:
    def save(self, appointment: Appointment):
        return AppointmentModel.objects.create(
            id=appointment.id,
            patient_id=appointment.patient_id,
            doctor_id=appointment.doctor_id,
            appointment_time=appointment.appointment_time,
            status=appointment.status,
        )

    def exists_by_doctor_and_time(self, doctor_id, appointment_time):
        return AppointmentModel.objects.filter(
            doctor_id=doctor_id,
            appointment_time=appointment_time
        ).exists()

    def list(self):
        return AppointmentModel.objects.all().order_by("appointment_time")

    def get(self, appointment_id):
        return AppointmentModel.objects.get(pk=appointment_id)
