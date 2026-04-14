from django.urls import path
from doctor.interfaces.views import (
    DoctorDetailView,
    DoctorListCreateView,
    DoctorAvailabilityView,
)

urlpatterns = [
    path("doctors/", DoctorListCreateView.as_view()),
    path("doctors/<uuid:pk>/", DoctorDetailView.as_view()),
    path("doctors/<uuid:pk>/availability/", DoctorAvailabilityView.as_view()),
]
