from decimal import Decimal

from django.utils.crypto import get_random_string

from accounts.models import User
from company.models import Company, CompanyEmployee
from services.models import Service


class FakeData:
    def email(self):
        return f"{get_random_string(10).lower()}@example.com"

    def password(self):
        return "StrongPass123!"

    def user(self, full_name=None, email=None):
        value = get_random_string(8)
        return User.objects.create_user(
            email=email or self.email(),
            full_name=full_name or f"Pessoa {value}",
            password=self.password(),
        )

    def company(self):
        value = get_random_string(8).lower()
        return Company.objects.create(
            name=f"Barbearia {value}",
            slug=f"barbearia-{value}",
        )

    def owner(self, company):
        user = self.user()
        CompanyEmployee.objects.create(
            user=user,
            company=company,
            role=User.Role.OWNER,
            is_active=True,
        )
        return user

    def service(self, company):
        value = get_random_string(8)
        return Service.objects.create(
            company=company,
            name=f"Servico {value}",
            price=Decimal("50.00"),
            duration_minutes=30,
            is_active=True,
        )
