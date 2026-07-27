import json
from datetime import time, timedelta
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

    def user(self, full_name=None, is_active=True):
        value = get_random_string(10).lower()
        return User.objects.create_user(
            email=f"{value}@example.com",
            full_name=full_name or f"Pessoa {value}",
            password="StrongPass123!",
            is_active=is_active,
        )

    def barber(self, company):
        return CompanyEmployee.objects.create(
            user=self.user(),
            company=company,
            role=User.Role.BARBER,
            is_active=True,
        )

    def service(self, company, price=Decimal("50.00")):
        value = get_random_string(8)
        return Service.objects.create(
            company=company,
            name=f"Servico {value}",
            price=price,
            duration_minutes=30,
            is_active=True,
        )

    def assignment(self, barber, service):
        return BarberService.objects.create(
            barber=barber,
            service=service,
            is_active=True,
        )

    def appointment(
        self,
        company,
        customer,
        barber,
        service,
        status=Appointment.Status.CONFIRMED,
    ):
        appointment_date = timezone.localdate() + timedelta(days=1)
        return Appointment.objects.create(
            company=company,
            customer=customer,
            barber=barber,
            service=service,
            appointment_date=appointment_date,
            start_time=time(9, 0),
            end_time=time(9, 30),
            status=status,
        )


class FakeHTTPResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")
