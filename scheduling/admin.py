from django.contrib import admin

from scheduling.models import Appointment, WorkingHour


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "company",
        "customer",
        "barber",
        "service",
        "appointment_date",
        "start_time",
        "end_time",
        "status",
    )
    search_fields = (
        "customer__email",
        "customer__full_name",
        "barber__user__full_name",
        "service__name",
        "company__name",
        "company__slug",
    )
    list_filter = ("company", "barber", "service", "appointment_date", "status")
    readonly_fields = ("created_at", "updated_at", "cancelled_at", "completed_at")


@admin.register(WorkingHour)
class WorkingHourAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "company",
        "weekday",
        "start_time",
        "end_time",
        "is_active",
    )
    search_fields = ("company__name", "company__slug")
    list_filter = ("company", "weekday", "is_active")
