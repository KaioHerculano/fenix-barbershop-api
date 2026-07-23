from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from app.schemas.catalog import working_hour_list_schema
from app.schemas.scheduling import (
    appointment_cancel_schema,
    appointment_create_list_schema,
    appointment_detail_schema,
    appointment_reschedule_schema,
    availability_schema,
)
from company.models import Company
from scheduling.models import Appointment, WorkingHour
from scheduling.selectors import (
    get_active_barber,
    get_active_company,
    get_active_service,
    list_available_slots,
)
from scheduling.serializers import (
    AppointmentCreateSerializer,
    AppointmentRescheduleSerializer,
    AppointmentSerializer,
    AvailabilityQuerySerializer,
    WorkingHourSerializer,
)
from scheduling.services import (
    cancel_appointment,
    create_appointment,
    reschedule_appointment,
)


class WorkingHourListView(ListAPIView):
    serializer_class = WorkingHourSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def get_company(self):
        return get_object_or_404(
            Company,
            slug=self.kwargs["company_slug"],
            is_active=True,
        )

    def get_queryset(self):
        return WorkingHour.objects.filter(
            company=self.get_company(),
            is_active=True,
        )

    @working_hour_list_schema
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AvailabilityView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @availability_schema
    def get(self, request, company_slug):
        serializer = AvailabilityQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        company = get_active_company(company_slug)
        service = get_active_service(company, serializer.validated_data["service_id"])
        barber = get_active_barber(company, serializer.validated_data["barber_id"])
        slots = list_available_slots(
            company,
            barber,
            service,
            serializer.validated_data["date"],
        )
        return Response(slots)


class AppointmentListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self, company_slug):
        return (
            Appointment.objects.filter(
                company__slug=company_slug,
                company__is_active=True,
                customer=self.request.user,
            )
            .select_related("company", "service", "barber__user")
            .order_by("-appointment_date", "-start_time")
        )

    @appointment_create_list_schema
    def get(self, request, company_slug):
        appointments = self.get_queryset(company_slug)
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)

    @appointment_create_list_schema
    def post(self, request, company_slug):
        serializer = AppointmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment = create_appointment(
            company_slug,
            request.user,
            serializer.validated_data,
        )
        response_serializer = AppointmentSerializer(appointment)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class AppointmentDetailView(RetrieveAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = "appointment_id"

    def get_queryset(self):
        return Appointment.objects.filter(
            company__slug=self.kwargs["company_slug"],
            company__is_active=True,
            customer=self.request.user,
        ).select_related("company", "service", "barber__user")

    @appointment_detail_schema
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AppointmentCancelView(APIView):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def get_appointment(self, company_slug, appointment_id):
        return get_object_or_404(
            Appointment.objects.select_related("company", "service", "barber__user"),
            id=appointment_id,
            company__slug=company_slug,
            company__is_active=True,
            customer=self.request.user,
        )

    @appointment_cancel_schema
    def patch(self, request, company_slug, appointment_id):
        appointment = cancel_appointment(
            self.get_appointment(company_slug, appointment_id)
        )
        serializer = AppointmentSerializer(appointment)
        return Response(serializer.data)


class AppointmentRescheduleView(AppointmentCancelView):
    @appointment_reschedule_schema
    def patch(self, request, company_slug, appointment_id):
        serializer = AppointmentRescheduleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment = reschedule_appointment(
            self.get_appointment(company_slug, appointment_id),
            serializer.validated_data,
        )
        response_serializer = AppointmentSerializer(appointment)
        return Response(response_serializer.data)
