# appointment/domain/repositories.py
class AppointmentRepository:
    def save(self, appointment):
        raise NotImplementedError

    def exists_by_doctor_and_time(self, doctor_id, appointment_time):
        raise NotImplementedError