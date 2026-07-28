from django.contrib import admin

from payments.models import Payment, PaymentWebhookEvent


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "customer_email",
        "company",
        "appointment",
        "amount",
        "status",
        "provider",
        "provider_payment_id",
        "created_at",
        "paid_at",
    ]
    list_filter = [
        "status",
        "provider",
        "payment_method",
        "appointment__company",
        "created_at",
        "paid_at",
    ]
    search_fields = [
        "id",
        "user__email",
        "user__full_name",
        "user__phone",
        "appointment__id",
        "appointment__company__name",
        "appointment__company__slug",
        "provider_payment_id",
        "idempotency_key",
    ]
    readonly_fields = [
        "id",
        "user",
        "appointment",
        "amount",
        "status",
        "provider",
        "provider_payment_id",
        "idempotency_key",
        "payment_method",
        "checkout_url",
        "payment_code",
        "qr_code_base64",
        "provider_payload",
        "expires_at",
        "paid_at",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at"]

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("user", "appointment__company", "appointment__service")
        )

    @admin.display(description="Cliente", ordering="user__email")
    def customer_email(self, obj):
        return obj.user.email

    @admin.display(description="Empresa", ordering="appointment__company__name")
    def company(self, obj):
        return obj.appointment.company


@admin.register(PaymentWebhookEvent)
class PaymentWebhookEventAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "provider",
        "provider_event_id",
        "provider_payment_id",
        "event_type",
        "action",
        "processed_at",
        "created_at",
    ]
    list_filter = ["provider", "event_type", "action", "processed_at", "created_at"]
    search_fields = ["id", "provider_event_id", "provider_payment_id"]
    readonly_fields = [
        "id",
        "provider",
        "provider_event_id",
        "provider_payment_id",
        "event_type",
        "action",
        "raw_payload",
        "processed_at",
        "created_at",
    ]
    ordering = ["-created_at"]

    def has_add_permission(self, request):
        return False
