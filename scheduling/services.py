from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from company.models import CompanyEmployee
from scheduling.models import Appointment
from scheduling.selectors import (
    get_active_barber,
    get_active_company,
    get_active_service,
    validate_available_slot,
)


def create_appointment(company_slug, customer, data):
    with transaction.atomic():
        company = get_active_company(company_slug)
        service = get_active_service(company, data["service_id"])
        barber = CompanyEmployee.objects.select_for_update().get(
            id=get_active_barber(company, data["barber_id"]).id
        )
        end_time = validate_available_slot(
            company,
            barber,
            service,
            data["appointment_date"],
            data["start_time"],
        )
        return Appointment.objects.create(
            company=company,
            customer=customer,
            barber=barber,
            service=service,
            appointment_date=data["appointment_date"],
            start_time=data["start_time"],
            end_time=end_time,
            status=Appointment.Status.CONFIRMED,
            notes=data.get("notes", ""),
        )


def cancel_appointment(appointment):
    if appointment.status == Appointment.Status.CANCELLED:
        raise ValidationError({"status": "Agendamento já está cancelado."})
    if appointment.status == Appointment.Status.COMPLETED:
        raise ValidationError(
            {"status": "Agendamento concluído não pode ser cancelado."}
        )
    if appointment.status == Appointment.Status.EXPIRED:
        raise ValidationError(
            {"status": "Agendamento expirado não pode ser cancelado."}
        )

    appointment.status = Appointment.Status.CANCELLED
    appointment.cancelled_at = timezone.now()
    appointment.save(update_fields=["status", "cancelled_at", "updated_at"])
    return appointment


def reschedule_appointment(appointment, data):
    if appointment.status == Appointment.Status.CANCELLED:
        raise ValidationError(
            {"status": "Agendamento cancelado não pode ser reagendado."}
        )
    if appointment.status == Appointment.Status.COMPLETED:
        raise ValidationError(
            {"status": "Agendamento concluído não pode ser reagendado."}
        )
    if appointment.status == Appointment.Status.EXPIRED:
        raise ValidationError(
            {"status": "Agendamento expirado não pode ser reagendado."}
        )

    with transaction.atomic():
        barber = CompanyEmployee.objects.select_for_update().get(
            id=appointment.barber_id
        )
        Appointment.objects.select_for_update().filter(id=appointment.id).exists()
        original_status = appointment.status
        appointment.status = Appointment.Status.CANCELLED
        appointment.save(update_fields=["status", "updated_at"])
        try:
            end_time = validate_available_slot(
                appointment.company,
                barber,
                appointment.service,
                data["appointment_date"],
                data["start_time"],
            )
        except Exception:
            appointment.status = original_status
            appointment.save(update_fields=["status", "updated_at"])
            raise

        appointment.appointment_date = data["appointment_date"]
        appointment.start_time = data["start_time"]
        appointment.end_time = end_time
        appointment.status = original_status
        appointment.save(
            update_fields=[
                "appointment_date",
                "start_time",
                "end_time",
                "status",
                "updated_at",
            ]
        )
        return appointment
