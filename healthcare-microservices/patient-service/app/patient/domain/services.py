class PatientValidationService:
    @staticmethod
    def normalize_phone(phone: str) -> str:
        normalized = "".join(char for char in phone if char.isdigit() or char == "+")
        if len(normalized) < 9:
            raise ValueError("Phone number is invalid")
        return normalized
