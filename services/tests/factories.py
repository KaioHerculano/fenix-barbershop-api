from decimal import Decimal

from django.utils.crypto import get_random_string

from company.models import Company
from services.models import Service


class FakeData:
    def company(self, is_active=True):
        value = get_random_string(8).lower()
        return Company.objects.create(
            name=f"Barbearia {value}",
            slug=f"barbearia-{value}",
            is_active=is_active,
        )

    def service(self, company, is_active=True, name=None):
        value = get_random_string(8)
        return Service.objects.create(
            company=company,
            name=name or f"Corte {value}",
            description=f"Servico {value}",
            price=Decimal("45.00"),
            duration_minutes=45,
            is_active=is_active,
        )
