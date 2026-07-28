from django import forms
from django.contrib import admin

from loyalty.models import LoyaltyCard, LoyaltyTransaction
from loyalty.services import adjust_points


class LoyaltyTransactionAdjustmentForm(forms.ModelForm):
    class Meta:
        model = LoyaltyTransaction
        fields = ("company", "user", "points", "description")


@admin.register(LoyaltyCard)
class LoyaltyCardAdmin(admin.ModelAdmin):
    list_display = ("user", "company", "points_balance", "created_at", "updated_at")
    list_filter = ("company", "created_at", "updated_at")
    search_fields = ("user__email", "user__full_name", "company__name", "company__slug")
    readonly_fields = ("id", "points_balance", "created_at", "updated_at")
    autocomplete_fields = ("user", "company")
    ordering = ("company__name", "user__full_name")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "company")


@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(admin.ModelAdmin):
    form = LoyaltyTransactionAdjustmentForm
    list_display = ("user", "company", "type", "points", "appointment", "created_at")
    list_filter = ("company", "type", "created_at")
    search_fields = (
        "user__email",
        "user__full_name",
        "company__name",
        "company__slug",
        "description",
    )
    readonly_fields = (
        "id",
        "card",
        "type",
        "appointment",
        "created_at",
    )
    autocomplete_fields = ("company", "user", "card", "appointment")
    ordering = ("-created_at",)

    def get_fields(self, request, obj=None):
        if obj:
            return (
                "id",
                "card",
                "company",
                "user",
                "appointment",
                "type",
                "points",
                "description",
                "created_at",
            )
        return ("company", "user", "points", "description")

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return (
                "id",
                "card",
                "company",
                "user",
                "appointment",
                "type",
                "points",
                "description",
                "created_at",
            )
        return ("id", "card", "type", "appointment", "created_at")

    def save_model(self, request, obj, form, change):
        if change:
            return
        transaction = adjust_points(
            obj.user,
            obj.company,
            obj.points,
            obj.description,
        )
        obj.id = transaction.id
        obj.card = transaction.card
        obj.company = transaction.company
        obj.user = transaction.user
        obj.appointment = transaction.appointment
        obj.type = transaction.type
        obj.points = transaction.points
        obj.description = transaction.description
        obj.created_at = transaction.created_at

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("card", "company", "user", "appointment")
        )
