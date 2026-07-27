from decimal import Decimal

from django.utils.crypto import get_random_string

from accounts.models import User
from company.models import Company, CompanyEmployee
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

    def employee(self, company, role=User.Role.BARBER, is_active=True, user=None):
        return CompanyEmployee.objects.create(
            user=user or self.user(),
            company=company,
            role=role,
            is_active=is_active,
        )

    def service(self, company, is_active=True):
        value = get_random_string(8)
        return Service.objects.create(
            company=company,
            name=f"Servico {value}",
            price=Decimal("50.00"),
            duration_minutes=50,
            is_active=is_active,
        )
