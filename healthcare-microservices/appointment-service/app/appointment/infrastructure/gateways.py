# appointment/infrastructure/gateways.py
import os
import requests

PATIENT_SERVICE_URL = os.getenv("PATIENT_SERVICE_URL")
DOCTOR_SERVICE_URL = os.getenv("DOCTOR_SERVICE_URL")

class PatientGateway:
    def exists(self, patient_id):
        response = requests.get(f"{PATIENT_SERVICE_URL}/patients/{patient_id}/", timeout=5)
        return response.status_code == 200

class DoctorGateway:
    def exists(self, doctor_id):
        response = requests.get(f"{DOCTOR_SERVICE_URL}/doctors/{doctor_id}/", timeout=5)
        return response.status_code == 200

    def is_available(self, doctor_id, appointment_time):
        response = requests.get(
            f"{DOCTOR_SERVICE_URL}/doctors/{doctor_id}/availability/",
            params={"appointment_time": appointment_time.isoformat()},
            timeout=5,
        )
        if response.status_code != 200:
            return False
        return response.json().get("available", False)
