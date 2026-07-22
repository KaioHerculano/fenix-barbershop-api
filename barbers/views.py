from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from app.schemas.catalog import (
    barber_detail_schema,
    barber_list_schema,
    barber_services_schema,
)
from barbers.serializers import BarberSerializer
from company.models import Company, CompanyEmployee
from services.serializers import ServiceSerializer


class CompanyBarberMixin:
    serializer_class = BarberSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    lookup_url_kwarg = "barber_id"

    def get_company(self):
        return get_object_or_404(
            Company,
            slug=self.kwargs["company_slug"],
            is_active=True,
        )

    def get_queryset(self):
        return (
            CompanyEmployee.objects.filter(
                company=self.get_company(),
                role=User.Role.BARBER,
                is_active=True,
                user__is_active=True,
            )
            .select_related("user", "company")
            .prefetch_related("barber_services__service")
        )


class BarberListView(CompanyBarberMixin, ListAPIView):
    @barber_list_schema
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class BarberDetailView(CompanyBarberMixin, RetrieveAPIView):
    @barber_detail_schema
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class BarberServicesView(CompanyBarberMixin, APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @barber_services_schema
    def get(self, request, company_slug, barber_id):
        barber = get_object_or_404(self.get_queryset(), id=barber_id)
        services = [
            assignment.service
            for assignment in barber.barber_services.filter(
                is_active=True,
                service__is_active=True,
            ).select_related("service")
        ]
        serializer = ServiceSerializer(services, many=True)
        return Response(serializer.data)
