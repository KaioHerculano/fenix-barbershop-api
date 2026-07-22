from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from app.schemas.catalog import working_hour_list_schema
from company.models import Company
from scheduling.models import WorkingHour
from scheduling.serializers import WorkingHourSerializer


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
