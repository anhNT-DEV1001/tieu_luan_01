# appointment/domain/entities.py
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Appointment:
    id: UUID
    patient_id: UUID
    doctor_id: UUID
    appointment_time: datetime
    status: str
    created_at: datetime | None = None

    @classmethod
    def create(cls, id, patient_id, doctor_id, appointment_time):
        return cls(
            id=id,
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_time=appointment_time,
            status="SCHEDULED",
        )
