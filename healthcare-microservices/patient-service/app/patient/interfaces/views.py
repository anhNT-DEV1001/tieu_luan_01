# patient/interfaces/views.py
from django.http import Http404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from patient.application.use_cases import (
    CreatePatientUseCase,
    GetPatientUseCase,
    ListPatientsUseCase,
)
from patient.infrastructure.repositories import DjangoPatientRepository
from patient.interfaces.serializers import PatientSerializer


class PatientListCreateView(APIView):
    serializer_class = PatientSerializer

    def get(self, request):
        patients = ListPatientsUseCase(DjangoPatientRepository()).execute()
        serializer = self.serializer_class(patients, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            patient = CreatePatientUseCase(DjangoPatientRepository()).execute(
                full_name=serializer.validated_data["full_name"],
                phone=serializer.validated_data["phone"],
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        output = self.serializer_class(patient)
        return Response(output.data, status=status.HTTP_201_CREATED)


class PatientDetailView(generics.RetrieveAPIView):
    serializer_class = PatientSerializer

    def get_object(self):
        try:
            return GetPatientUseCase(DjangoPatientRepository()).execute(self.kwargs["pk"])
        except Exception as exc:
            if exc.__class__.__name__ == "DoesNotExist":
                raise Http404 from exc
            raise
