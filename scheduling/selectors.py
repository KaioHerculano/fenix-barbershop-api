from datetime import datetime, timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from accounts.models import User
from barbers.models import BarberService
from company.models import Company, CompanyEmployee
from scheduling.models import Appointment, WorkingHour
from services.models import Service

SLOT_STEP_MINUTES = 15


def get_active_company(company_slug):
    return get_object_or_404(Company, slug=company_slug, is_active=True)


def get_active_service(company, service_id):
    return get_object_or_404(Service, id=service_id, company=company, is_active=True)


def get_active_barber(company, barber_id):
    return get_object_or_404(
        CompanyEmployee.objects.select_related("user", "company"),
        id=barber_id,
        company=company,
        role=User.Role.BARBER,
        is_active=True,
        user__is_active=True,
    )


def validate_barber_service(company, barber, service):
    exists = BarberService.objects.filter(
        barber=barber,
        service=service,
        barber__company=company,
        service__company=company,
        is_active=True,
        service__is_active=True,
    ).exists()
    if not exists:
        raise ValidationError(
            {"barber_id": "Barbeiro não executa este serviço nesta empresa."}
        )


def get_working_hours(company, appointment_date):
    weekday = appointment_date.weekday()
    return WorkingHour.objects.filter(
        company=company,
        weekday=weekday,
        is_active=True,
    ).order_by("start_time")


def combine_local(appointment_date, appointment_time):
    value = datetime.combine(appointment_date, appointment_time)
    return timezone.make_aware(value, timezone.get_current_timezone())


def calculate_end_time(start_time, duration_minutes):
    value = datetime.combine(timezone.localdate(), start_time) + timedelta(
        minutes=duration_minutes
    )
    return value.time()


def is_past_slot(appointment_date, start_time):
    return combine_local(appointment_date, start_time) <= timezone.localtime()


def appointment_conflicts(company, barber, appointment_date, start_time, end_time):
    return Appointment.objects.filter(
        company=company,
        barber=barber,
        appointment_date=appointment_date,
        status__in=Appointment.BLOCKING_STATUSES,
        start_time__lt=end_time,
        end_time__gt=start_time,
    ).exists()


def slot_fits_working_hours(company, appointment_date, start_time, end_time):
    return (
        get_working_hours(company, appointment_date)
        .filter(
            start_time__lte=start_time,
            end_time__gte=end_time,
        )
        .exists()
    )


def validate_available_slot(company, barber, service, appointment_date, start_time):
    validate_barber_service(company, barber, service)
    if is_past_slot(appointment_date, start_time):
        raise ValidationError({"start_time": "Horário não pode estar no passado."})

    end_time = calculate_end_time(start_time, service.duration_minutes)
    if end_time <= start_time:
        raise ValidationError({"start_time": "Horário deve terminar no mesmo dia."})

    if not slot_fits_working_hours(company, appointment_date, start_time, end_time):
        raise ValidationError({"start_time": "Horário fora do funcionamento."})

    if appointment_conflicts(company, barber, appointment_date, start_time, end_time):
        raise ValidationError(
            {"start_time": "Horário indisponível para este barbeiro."}
        )

    return end_time


def list_available_slots(company, barber, service, appointment_date):
    validate_barber_service(company, barber, service)
    slots = []
    step = timedelta(minutes=SLOT_STEP_MINUTES)
    duration = timedelta(minutes=service.duration_minutes)

    for working_hour in get_working_hours(company, appointment_date):
        current = datetime.combine(appointment_date, working_hour.start_time)
        work_end = datetime.combine(appointment_date, working_hour.end_time)

        while current + duration <= work_end:
            start_time = current.time()
            end_time = (current + duration).time()
            if not is_past_slot(
                appointment_date, start_time
            ) and not appointment_conflicts(
                company,
                barber,
                appointment_date,
                start_time,
                end_time,
            ):
                slots.append(
                    {
                        "start_time": start_time.strftime("%H:%M"),
                        "end_time": end_time.strftime("%H:%M"),
                    }
                )
            current += step

    return slots
