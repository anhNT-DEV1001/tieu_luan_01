from patient.domain.services import PatientValidationService


class CreatePatientUseCase:
    def __init__(self, patient_repo):
        self.patient_repo = patient_repo

    def execute(self, *, full_name, phone):
        if not full_name.strip():
            raise ValueError("Full name is required")

        normalized_phone = PatientValidationService.normalize_phone(phone)
        return self.patient_repo.create(full_name=full_name.strip(), phone=normalized_phone)


class GetPatientUseCase:
    def __init__(self, patient_repo):
        self.patient_repo = patient_repo

    def execute(self, patient_id):
        return self.patient_repo.get(patient_id)


class ListPatientsUseCase:
    def __init__(self, patient_repo):
        self.patient_repo = patient_repo

    def execute(self):
        return self.patient_repo.list()
