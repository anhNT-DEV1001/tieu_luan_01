class PatientRepository:
    def create(self, *, full_name, phone):
        raise NotImplementedError

    def get(self, patient_id):
        raise NotImplementedError

    def list(self):
        raise NotImplementedError
