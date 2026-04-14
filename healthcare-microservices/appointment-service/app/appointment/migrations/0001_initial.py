import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AppointmentModel",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("patient_id", models.UUIDField()),
                ("doctor_id", models.UUIDField()),
                ("appointment_time", models.DateTimeField()),
                ("status", models.CharField(max_length=50)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "appointments"},
        ),
        migrations.AddConstraint(
            model_name="appointmentmodel",
            constraint=models.UniqueConstraint(
                fields=("doctor_id", "appointment_time"),
                name="unique_doctor_appointment_time",
            ),
        ),
    ]
