from django.contrib import admin, messages
from django.utils import timezone

from scheduling.models import Appointment, WorkingHour
from scheduling.services import cancel_appointment, complete_appointment_record


class AppointmentDateListFilter(admin.SimpleListFilter):
    title = "periodo"
    parameter_name = "period"

    def lookups(self, request, model_admin):
        return (
            ("today", "Hoje"),
            ("upcoming", "Proximos"),
            ("past", "Passados"),
        )

    def queryset(self, request, queryset):
        today = timezone.localdate()
        if self.value() == "today":
            return queryset.filter(appointment_date=today)
        if self.value() == "upcoming":
            return queryset.filter(appointment_date__gte=today)
        if self.value() == "past":
            return queryset.filter(appointment_date__lt=today)
        return queryset


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
        "payment_status",
        "created_at",
    )
    search_fields = (
        "customer__email",
        "customer__full_name",
        "customer__phone",
        "barber__user__full_name",
        "barber__user__email",
        "service__name",
        "company__name",
        "company__slug",
    )
    list_filter = (
        AppointmentDateListFilter,
        "status",
        "company",
        "barber",
        "service",
        "appointment_date",
    )
    ordering = ("appointment_date", "start_time")
    readonly_fields = ("id", "created_at", "updated_at", "cancelled_at", "completed_at")
    autocomplete_fields = ("company", "customer", "barber", "service")
    actions = ("cancel_selected_appointments", "complete_selected_appointments")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "company",
                "customer",
                "barber__user",
                "service",
            )
            .prefetch_related("payments")
        )

    @admin.display(description="Pagamento")
    def payment_status(self, obj):
        payment = next(iter(obj.payments.all()), None)
        if not payment:
            return "-"
        return payment.status

    @admin.action(description="Cancelar agendamentos selecionados")
    def cancel_selected_appointments(self, request, queryset):
        cancelled = 0
        skipped = 0
        for appointment in queryset.select_related("company", "customer", "service"):
            try:
                cancel_appointment(appointment)
                cancelled += 1
            except Exception:
                skipped += 1
        self.message_user(
            request,
            f"{cancelled} agendamento(s) cancelado(s), {skipped} ignorado(s).",
            messages.INFO,
        )

    @admin.action(description="Marcar agendamentos como concluidos")
    def complete_selected_appointments(self, request, queryset):
        completed = 0
        skipped = 0
        for appointment in queryset.select_related(
            "company",
            "customer",
            "service",
            "barber__user",
        ):
            try:
                complete_appointment_record(appointment)
                completed += 1
            except Exception:
                skipped += 1
        self.message_user(
            request,
            f"{completed} agendamento(s) concluido(s), {skipped} ignorado(s).",
            messages.INFO,
        )


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
    list_filter = ("company", "weekday", "is_active", "created_at")
    ordering = ("company__name", "weekday", "start_time")
    readonly_fields = ("id", "created_at", "updated_at")
    autocomplete_fields = ("company",)
    actions = ("activate_working_hours", "deactivate_working_hours")

    @admin.action(description="Ativar horarios selecionados")
    def activate_working_hours(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Desativar horarios selecionados")
    def deactivate_working_hours(self, request, queryset):
        queryset.update(is_active=False)
