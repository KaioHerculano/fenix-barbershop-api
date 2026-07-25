from rest_framework import serializers

from payments.models import Payment


class PaymentCreateSerializer(serializers.Serializer):
    appointment_id = serializers.UUIDField()


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
            "pix_qr_code",
            "pix_copy_paste",
            "paid_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
