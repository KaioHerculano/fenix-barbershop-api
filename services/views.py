from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny

from app.schemas.catalog import service_detail_schema, service_list_schema
from company.models import Company
from services.models import Service
from services.serializers import ServiceSerializer


class CompanyServiceMixin:
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    lookup_url_kwarg = "service_id"

    def get_company(self):
        return get_object_or_404(
            Company,
            slug=self.kwargs["company_slug"],
            is_active=True,
        )

    def get_queryset(self):
        return Service.objects.filter(
            company=self.get_company(),
            is_active=True,
        )


class ServiceListView(CompanyServiceMixin, ListAPIView):
    @service_list_schema
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ServiceDetailView(CompanyServiceMixin, RetrieveAPIView):
    @service_detail_schema
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
