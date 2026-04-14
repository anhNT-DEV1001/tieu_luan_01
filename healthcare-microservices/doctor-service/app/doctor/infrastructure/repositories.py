from doctor.infrastructure.models import DoctorModel


class DjangoDoctorRepository:
    def create(self, *, full_name, specialty):
        return DoctorModel.objects.create(full_name=full_name, specialty=specialty)

    def get(self, doctor_id):
        return DoctorModel.objects.get(pk=doctor_id)

    def list(self):
        return DoctorModel.objects.all().order_by("-created_at")
