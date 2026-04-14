# appointment/infrastructure/models.py
import uuid
from django.db import models

class AppointmentModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient_id = models.UUIDField()
    doctor_id = models.UUIDField()
    appointment_time = models.DateTimeField()
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "appointments"
        constraints = [
            models.UniqueConstraint(
                fields=["doctor_id", "appointment_time"],
                name="unique_doctor_appointment_time"
            )
        ]