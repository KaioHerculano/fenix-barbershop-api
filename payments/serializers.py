from rest_framework import serializers

from payments.models import Payment


class PaymentCreateSerializer(serializers.Serializer):
    appointment_id = serializers.UUIDField()


class PaymentWebhookSerializer(serializers.Serializer):
    id = serializers.CharField(required=False, allow_blank=True)
    type = serializers.CharField(required=False, allow_blank=True)
    action = serializers.CharField(required=False, allow_blank=True)
    data = serializers.DictField(required=False)
    provider_payment_id = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True)


class PaymentSerializer(serializers.ModelSerializer):
    appointment_id = serializers.UUIDField(source="appointment.id", read_only=True)
    company_slug = serializers.CharField(
        source="appointment.company.slug", read_only=True
    )
    service_name = serializers.CharField(
        source="appointment.service.name", read_only=True
    )

    class Meta:
        model = Payment
        fields = [
            "id",
            "appointment_id",
            "company_slug",
            "service_name",
            "amount",
            "status",
            "provider",
            "provider_payment_id",
            "payment_method",
            "checkout_url",
            "payment_code",
            "qr_code_base64",
            "expires_at",
            "paid_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
