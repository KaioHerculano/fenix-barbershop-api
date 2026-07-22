from django.contrib import admin

from services.models import Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "company",
        "price",
        "duration_minutes",
        "is_active",
    )
    search_fields = ("name", "company__name", "company__slug")
    list_filter = ("company", "is_active")
