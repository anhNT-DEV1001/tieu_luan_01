from rest_framework import serializers

from doctor.infrastructure.models import DoctorModel


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorModel
        fields = ["id", "full_name", "specialty", "created_at"]
        read_only_fields = ["id", "created_at"]
