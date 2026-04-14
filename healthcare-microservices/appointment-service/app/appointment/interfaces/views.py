# appointment/interfaces/views.py
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from appointment.interfaces.serializers import AppointmentSerializer, BookAppointmentSerializer
from appointment.application.use_cases import (
    BookAppointmentUseCase,
    GetAppointmentUseCase,
    ListAppointmentsUseCase,
)
from appointment.infrastructure.repositories import DjangoAppointmentRepository
from appointment.infrastructure.gateways import PatientGateway, DoctorGateway


class AppointmentListCreateView(APIView):
    def get(self, request):
        appointments = ListAppointmentsUseCase(DjangoAppointmentRepository()).execute()
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = BookAppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = BookAppointmentUseCase(
            appointment_repo=DjangoAppointmentRepository(),
            patient_gateway=PatientGateway(),
            doctor_gateway=DoctorGateway(),
        )

        try:
            appointment = use_case.execute(
                patient_id=serializer.validated_data["patient_id"],
                doctor_id=serializer.validated_data["doctor_id"],
                appointment_time=serializer.validated_data["appointment_time"],
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        output = AppointmentSerializer(appointment)
        return Response(output.data, status=status.HTTP_201_CREATED)


class AppointmentDetailView(APIView):
    def get(self, request, pk):
        try:
            appointment = GetAppointmentUseCase(DjangoAppointmentRepository()).execute(pk)
        except Exception as exc:
            if exc.__class__.__name__ == "DoesNotExist":
                raise Http404 from exc
            raise

        serializer = AppointmentSerializer(appointment)
        return Response(serializer.data)
