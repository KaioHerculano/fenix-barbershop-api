from django.contrib import admin

from payments.models import Payment


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
