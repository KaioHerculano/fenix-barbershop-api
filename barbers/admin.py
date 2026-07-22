from django.contrib import admin

from barbers.models import BarberService


@admin.register(BarberService)
class BarberServiceAdmin(admin.ModelAdmin):
    list_display = ("id", "barber", "service", "is_active", "created_at")
    search_fields = (
        "barber__user__full_name",
        "barber__user__email",
        "service__name",
    )
    list_filter = ("barber__company", "is_active")
