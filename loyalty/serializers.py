from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from loyalty.models import LoyaltyCard, LoyaltyTransaction


class LoyaltyCardSerializer(serializers.ModelSerializer):
    company_slug = serializers.CharField(source="company.slug", read_only=True)
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = LoyaltyCard
        fields = [
            "id",
            "company_slug",
            "company_name",
            "points_balance",
            "created_at",
            "updated_at",
        ]


class LoyaltySummarySerializer(serializers.Serializer):
    total_points_balance = serializers.IntegerField()
    earned_points = serializers.IntegerField()
    redeemed_points = serializers.IntegerField()
    adjustment_points = serializers.IntegerField()
    cards = LoyaltyCardSerializer(many=True)


class LoyaltyTransactionSerializer(serializers.ModelSerializer):
    company_slug = serializers.CharField(source="company.slug", read_only=True)
    company_name = serializers.CharField(source="company.name", read_only=True)
    appointment_id = serializers.SerializerMethodField()
    service_name = serializers.SerializerMethodField()

    class Meta:
        model = LoyaltyTransaction
        fields = [
            "id",
            "company_slug",
            "company_name",
            "appointment_id",
            "service_name",
            "type",
            "points",
            "description",
            "created_at",
        ]

    @extend_schema_field(serializers.UUIDField(allow_null=True))
    def get_appointment_id(self, obj):
        if not obj.appointment_id:
            return None
        return obj.appointment_id

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_service_name(self, obj):
        if not obj.appointment_id:
            return None
        return obj.appointment.service.name


class LoyaltyRedeemSerializer(serializers.Serializer):
    company_slug = serializers.SlugField()
    points = serializers.IntegerField(min_value=1)
    description = serializers.CharField(
        required=False, allow_blank=True, max_length=255
    )
