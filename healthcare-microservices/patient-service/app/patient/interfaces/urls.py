# patient/interfaces/urls.py
from django.urls import path
from patient.interfaces.views import PatientDetailView, PatientListCreateView

urlpatterns = [
    path("patients/", PatientListCreateView.as_view()),
    path("patients/<uuid:pk>/", PatientDetailView.as_view()),
]
