class DoctorRepository:
    def create(self, *, full_name, specialty):
        raise NotImplementedError

    def get(self, doctor_id):
        raise NotImplementedError

    def list(self):
        raise NotImplementedError
