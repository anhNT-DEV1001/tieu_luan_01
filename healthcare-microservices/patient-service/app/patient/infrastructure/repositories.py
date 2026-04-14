from patient.infrastructure.models import PatientModel


class DjangoPatientRepository:
    def create(self, *, full_name, phone):
        return PatientModel.objects.create(full_name=full_name, phone=phone)

    def get(self, patient_id):
        return PatientModel.objects.get(pk=patient_id)

    def list(self):
        return PatientModel.objects.all().order_by("-created_at")
