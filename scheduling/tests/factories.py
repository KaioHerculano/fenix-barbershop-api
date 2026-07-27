from datetime import date, time, timedelta
from decimal import Decimal

from django.utils import timezone
from django.utils.crypto import get_random_string

from accounts.models import User
from barbers.models import BarberService
from company.models import Company, CompanyEmployee
from scheduling.models import Appointment, WorkingHour
from services.models import Service


class FakeData:
    def company(self, is_active=True):
        value = get_random_string(8).lower()
        return Company.objects.create(
            name=f"Barbearia {value}",
            slug=f"barbearia-{value}",
            is_active=is_active,
        )

    def user(self, full_name=None, is_active=True):
        value = get_random_string(10).lower()
        return User.objects.create_user(
            email=f"{value}@example.com",
            full_name=full_name or f"Pessoa {value}",
            password="StrongPass123!",
            is_active=is_active,
        )

    def barber(self, company, is_active=True, user=None):
        return CompanyEmployee.objects.create(
            user=user or self.user(),
            company=company,
            role=User.Role.BARBER,
            is_active=is_active,
        )

    def owner(self, company):
        return CompanyEmployee.objects.create(
            user=self.user(),
            company=company,
            role=User.Role.OWNER,
            is_active=True,
        )

    def service(self, company, duration_minutes=30, is_active=True):
        value = get_random_string(8)
        return Service.objects.create(
            company=company,
            name=f"Servico {value}",
            price=Decimal("50.00"),
            duration_minutes=duration_minutes,
            is_active=is_active,
        )

    def assignment(self, barber, service, is_active=True):
        return BarberService.objects.create(
            barber=barber,
            service=service,
            is_active=is_active,
        )

    def future_date(self, days_ahead=1):
        return timezone.localdate() + timedelta(days=days_ahead)

    def working_hour(
        self,
        company,
        appointment_date=None,
        start_time=time(9, 0),
        end_time=time(11, 0),
        is_active=True,
    ):
        value = appointment_date or self.future_date()
        return WorkingHour.objects.create(
            company=company,
            weekday=value.weekday(),
            start_time=start_time,
            end_time=end_time,
            is_active=is_active,
        )

    def appointment(
        self,
        company,
        customer,
        barber,
        service,
        appointment_date,
        start_time=time(9, 0),
        status=Appointment.Status.CONFIRMED,
    ):
        start_dt = timezone.datetime.combine(date.today(), start_time)
        end_time = (start_dt + timedelta(minutes=service.duration_minutes)).time()
        return Appointment.objects.create(
            company=company,
            customer=customer,
            barber=barber,
            service=service,
            appointment_date=appointment_date,
            start_time=start_time,
            end_time=end_time,
            status=status,
        )
