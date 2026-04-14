class DoctorValidationService:
    @staticmethod
    def validate_specialty(specialty: str) -> str:
        specialty = specialty.strip()
        if not specialty:
            raise ValueError("Specialty is required")
        return specialty
