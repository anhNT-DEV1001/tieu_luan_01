from django.urls import include, path

urlpatterns = [
    path("", include("appointment.interfaces.urls")),
]
