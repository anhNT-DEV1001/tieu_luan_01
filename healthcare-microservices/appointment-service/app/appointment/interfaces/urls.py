from django.urls import path
from appointment.interfaces.views import AppointmentDetailView, AppointmentListCreateView

urlpatterns = [
    path("appointments/", AppointmentListCreateView.as_view()),
    path("appointments/<uuid:pk>/", AppointmentDetailView.as_view()),
]
