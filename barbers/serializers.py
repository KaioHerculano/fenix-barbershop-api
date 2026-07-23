from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from company.models import CompanyEmployee
from services.serializers import ServiceSerializer


class BarberSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    services = serializers.SerializerMethodField()

    class Meta:
        model = CompanyEmployee
        fields = ["id", "full_name", "services"]

    @extend_schema_field(ServiceSerializer(many=True))
    def get_services(self, obj):
        assignments = obj.barber_services.filter(
            is_active=True,
            service__is_active=True,
        ).select_related("service")
        return [
            ServiceSerializer(assignment.service).data for assignment in assignments
        ]
