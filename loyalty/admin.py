from django.contrib import admin

from loyalty.models import LoyaltyCard, LoyaltyTransaction


@admin.register(LoyaltyCard)
class LoyaltyCardAdmin(admin.ModelAdmin):
    list_display = ("user", "company", "points_balance", "updated_at")
    list_filter = ("company",)
    search_fields = ("user__email", "user__full_name", "company__name", "company__slug")
    readonly_fields = ("created_at", "updated_at")


@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "company", "type", "points", "appointment", "created_at")
    list_filter = ("company", "type", "created_at")
    search_fields = (
        "user__email",
        "user__full_name",
        "company__name",
        "company__slug",
        "description",
    )
    readonly_fields = ("created_at",)
