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
    search_fields = ("name", "description", "company__name", "company__slug")
    list_filter = ("company", "is_active", "duration_minutes", "created_at")
    ordering = ("company__name", "name")
    readonly_fields = ("id", "created_at", "updated_at")
    autocomplete_fields = ("company",)
    actions = ("activate_services", "deactivate_services")

    @admin.action(description="Ativar servicos selecionados")
    def activate_services(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Desativar servicos selecionados")
    def deactivate_services(self, request, queryset):
        queryset.update(is_active=False)
