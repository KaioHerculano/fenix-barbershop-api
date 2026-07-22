from django.contrib import admin

from scheduling.models import WorkingHour


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
