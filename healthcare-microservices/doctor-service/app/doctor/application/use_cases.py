from doctor.domain.services import DoctorValidationService


class CreateDoctorUseCase:
    def __init__(self, doctor_repo):
        self.doctor_repo = doctor_repo

    def execute(self, *, full_name, specialty):
        if not full_name.strip():
            raise ValueError("Full name is required")

        return self.doctor_repo.create(
            full_name=full_name.strip(),
            specialty=DoctorValidationService.validate_specialty(specialty),
        )


class GetDoctorUseCase:
    def __init__(self, doctor_repo):
        self.doctor_repo = doctor_repo

    def execute(self, doctor_id):
        return self.doctor_repo.get(doctor_id)


class ListDoctorsUseCase:
    def __init__(self, doctor_repo):
        self.doctor_repo = doctor_repo

    def execute(self):
        return self.doctor_repo.list()
