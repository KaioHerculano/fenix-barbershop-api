from django.contrib import admin

from barbers.models import BarberService


@admin.register(BarberService)
class BarberServiceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "company",
        "barber_name",
        "barber_email",
        "service",
        "is_active",
        "created_at",
    )
    search_fields = (
        "barber__user__full_name",
        "barber__user__email",
        "service__name",
        "service__company__name",
        "service__company__slug",
    )
    list_filter = ("barber__company", "service", "is_active", "created_at")
    ordering = ("barber__company__name", "barber__user__full_name", "service__name")
    readonly_fields = ("id", "created_at", "updated_at")
    autocomplete_fields = ("barber", "service")
    actions = ("activate_assignments", "deactivate_assignments")

    @admin.display(description="Empresa", ordering="barber__company__name")
    def company(self, obj):
        return obj.barber.company

    @admin.display(description="Barbeiro", ordering="barber__user__full_name")
    def barber_name(self, obj):
        return obj.barber.user.full_name

    @admin.display(description="Email", ordering="barber__user__email")
    def barber_email(self, obj):
        return obj.barber.user.email

    @admin.action(description="Ativar vinculos selecionados")
    def activate_assignments(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Desativar vinculos selecionados")
    def deactivate_assignments(self, request, queryset):
        queryset.update(is_active=False)
