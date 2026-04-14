class AppointmentDomainService:
    @staticmethod
    def validate_status(status: str) -> str:
        allowed_statuses = {"SCHEDULED", "CANCELLED"}
        if status not in allowed_statuses:
            raise ValueError("Appointment status is invalid")
        return status
