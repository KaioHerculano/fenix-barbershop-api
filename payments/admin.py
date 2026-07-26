from django.contrib import admin

from payments.models import Payment, PaymentWebhookEvent


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "appointment",
        "amount",
        "status",
        "provider",
        "created_at",
        "paid_at",
    ]
    list_filter = ["status", "provider", "created_at", "paid_at"]
    search_fields = [
        "id",
        "user__email",
        "user__full_name",
        "appointment__id",
        "provider_payment_id",
        "idempotency_key",
    ]
    readonly_fields = ["id", "created_at", "updated_at", "paid_at"]


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
    readonly_fields = ["id", "created_at", "processed_at"]
