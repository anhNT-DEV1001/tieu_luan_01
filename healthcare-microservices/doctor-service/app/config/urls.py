from django.urls import include, path

urlpatterns = [
    path("", include("doctor.interfaces.urls")),
]
