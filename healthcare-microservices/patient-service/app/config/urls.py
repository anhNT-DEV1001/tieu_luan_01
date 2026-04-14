from django.urls import include, path

urlpatterns = [
    path("", include("patient.interfaces.urls")),
]
