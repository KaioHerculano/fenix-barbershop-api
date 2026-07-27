from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from django.utils.crypto import get_random_string

from accounts.models import User
from company.models import Company, CompanyEmployee, StaffInvitation
from scheduling.models import Appointment
from services.models import Service


class FakeData:
    def email(self):
        return f"{get_random_string(10).lower()}@example.com"

    def user(self):
        return User.objects.create_user(
            email=self.email(),
            full_name="Cliente Email",
            password="StrongPass123!",
        )

    def company(self):
        value = get_random_string(8).lower()
        return Company.objects.create(name=f"Barbearia {value}", slug=value)

    def service(self, company):
        return Service.objects.create(
            company=company,
            name="Corte",
            price=Decimal("45.00"),
            duration_minutes=30,
            is_active=True,
        )

    def barber(self, company):
        return CompanyEmployee.objects.create(
            user=self.user(),
            company=company,
            role=User.Role.BARBER,
            is_active=True,
        )

    def appointment(self):
        company = self.company()
        return Appointment.objects.create(
            company=company,
            customer=self.user(),
            barber=self.barber(company),
            service=self.service(company),
            appointment_date=timezone.localdate(),
            start_time=timezone.datetime(2026, 1, 1, 9, 0).time(),
            end_time=timezone.datetime(2026, 1, 1, 9, 30).time(),
            status=Appointment.Status.CONFIRMED,
        )

    def invitation(self):
        token, digest = StaffInvitation.build_token()
        company = self.company()
        return (
            StaffInvitation.objects.create(
                company=company,
                email=self.email(),
                role=User.Role.BARBER,
                invited_by=self.user(),
                token_digest=digest,
                expires_at=timezone.now() + timedelta(days=7),
            ),
            token,
        )
