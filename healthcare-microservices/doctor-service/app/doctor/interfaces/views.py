# doctor/interfaces/views.py
from django.http import Http404
from django.utils.dateparse import parse_datetime
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from doctor.application.use_cases import CreateDoctorUseCase, GetDoctorUseCase, ListDoctorsUseCase
from doctor.infrastructure.repositories import DjangoDoctorRepository
from doctor.interfaces.serializers import DoctorSerializer


class DoctorListCreateView(APIView):
    serializer_class = DoctorSerializer

    def get(self, request):
        doctors = ListDoctorsUseCase(DjangoDoctorRepository()).execute()
        serializer = self.serializer_class(doctors, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            doctor = CreateDoctorUseCase(DjangoDoctorRepository()).execute(
                full_name=serializer.validated_data["full_name"],
                specialty=serializer.validated_data["specialty"],
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        output = self.serializer_class(doctor)
        return Response(output.data, status=status.HTTP_201_CREATED)


class DoctorDetailView(generics.RetrieveAPIView):
    serializer_class = DoctorSerializer

    def get_object(self):
        try:
            return GetDoctorUseCase(DjangoDoctorRepository()).execute(self.kwargs["pk"])
        except Exception as exc:
            if exc.__class__.__name__ == "DoesNotExist":
                raise Http404 from exc
            raise

class DoctorAvailabilityView(APIView):
    def get(self, request, pk):
        try:
            GetDoctorUseCase(DjangoDoctorRepository()).execute(pk)
        except Exception as exc:
            if exc.__class__.__name__ == "DoesNotExist":
                return Response({"detail": "Doctor not found"}, status=404)
            raise

        appointment_time = request.query_params.get("appointment_time")
        parsed_time = parse_datetime(appointment_time) if appointment_time else None
        if appointment_time and parsed_time is None:
            return Response({"detail": "appointment_time is invalid"}, status=400)

        return Response({
            "doctor_id": str(pk),
            "available": True
        })
