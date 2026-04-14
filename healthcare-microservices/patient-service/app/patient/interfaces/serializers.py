# patient/interfaces/serializers.py
from rest_framework import serializers
from patient.infrastructure.models import PatientModel


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientModel
        fields = ["id", "full_name", "phone", "created_at"]
        read_only_fields = ["id", "created_at"]
