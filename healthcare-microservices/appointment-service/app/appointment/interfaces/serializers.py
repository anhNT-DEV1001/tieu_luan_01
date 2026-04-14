from rest_framework import serializers

from appointment.infrastructure.models import AppointmentModel


class BookAppointmentSerializer(serializers.Serializer):
    patient_id = serializers.UUIDField()
    doctor_id = serializers.UUIDField()
    appointment_time = serializers.DateTimeField()


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentModel
        fields = [
            "id",
            "patient_id",
            "doctor_id",
            "appointment_time",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "status", "created_at"]
