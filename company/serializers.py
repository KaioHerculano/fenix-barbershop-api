from rest_framework import serializers

from company.models import StaffInvitation
from services.models import Service


class StaffInvitationCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    full_name = serializers.CharField(required=False, allow_blank=True, max_length=255)
    service_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
    )

    def validate_service_ids(self, value):
        company = self.context["company"]
        found = set(
            Service.objects.filter(
                id__in=value,
                company=company,
                is_active=True,
            ).values_list("id", flat=True)
        )
        missing = [service_id for service_id in value if service_id not in found]
        if missing:
            raise serializers.ValidationError("Servico invalido para esta empresa.")
        return value


class StaffInvitationSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    services = serializers.SerializerMethodField()
    is_expired = serializers.BooleanField(read_only=True)
    is_accepted = serializers.BooleanField(read_only=True)

    class Meta:
        model = StaffInvitation
        fields = [
            "id",
            "company_name",
            "email",
            "full_name",
            "role",
            "services",
            "expires_at",
            "is_expired",
            "is_accepted",
            "accepted_at",
            "created_at",
        ]

    def get_services(self, obj):
        return [
            {"id": service.id, "name": service.name} for service in obj.services.all()
        ]


class StaffInvitationAcceptSerializer(serializers.Serializer):
    full_name = serializers.CharField(required=False, allow_blank=True, max_length=255)
    password = serializers.CharField(required=False, write_only=True)
    password_confirmation = serializers.CharField(required=False, write_only=True)


class StaffInvitationAcceptResponseSerializer(serializers.Serializer):
    company_slug = serializers.CharField()
    role = serializers.CharField()
    is_active = serializers.BooleanField()
