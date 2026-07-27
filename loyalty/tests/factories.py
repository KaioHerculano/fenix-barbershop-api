from datetime import date, time, timedelta
from decimal import Decimal

from django.utils import timezone
from django.utils.crypto import get_random_string

from accounts.models import User
from barbers.models import BarberService
from company.models import Company, CompanyEmployee
from scheduling.models import Appointment
from services.models import Service


class FakeData:
    def company(self, is_active=True):
        value = get_random_string(8).lower()
        return Company.objects.create(
            name=f"Barbearia {value}",
            slug=f"barbearia-{value}",
            is_active=is_active,
        )

    def user(self, full_name=None):
        value = get_random_string(10).lower()
        return User.objects.create_user(
            email=f"{value}@example.com",
            full_name=full_name or f"Pessoa {value}",
            password="StrongPass123!",
        )

    def employee(self, company, role, user=None, is_active=True):
        return CompanyEmployee.objects.create(
            user=user or self.user(),
            company=company,
            role=role,
            is_active=is_active,
        )

    def service(self, company, price=Decimal("50.00"), duration_minutes=30):
        value = get_random_string(8)
        return Service.objects.create(
            company=company,
            name=f"Servico {value}",
            price=price,
            duration_minutes=duration_minutes,
            is_active=True,
        )

    def appointment(
        self,
        company,
        customer,
        barber,
        service,
        status_value=Appointment.Status.CONFIRMED,
    ):
        start_time = time(9, 0)
        start_dt = timezone.datetime.combine(date.today(), start_time)
        return Appointment.objects.create(
            company=company,
            customer=customer,
            barber=barber,
            service=service,
            appointment_date=timezone.localdate() - timedelta(days=1),
            start_time=start_time,
            end_time=(start_dt + timedelta(minutes=service.duration_minutes)).time(),
            status=status_value,
            completed_at=(
                timezone.now() if status_value == Appointment.Status.COMPLETED else None
            ),
        )

    def assignment(self, barber, service):
        return BarberService.objects.create(
            barber=barber,
            service=service,
            is_active=True,
        )
