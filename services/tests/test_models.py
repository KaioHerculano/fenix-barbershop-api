from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from services.models import Service
from services.tests.factories import FakeData


class ServiceModelTests(TestCase):
    def setUp(self):
        self.fake = FakeData()
        self.company = self.fake.company()

    def test_create_valid_service(self):
        service = self.fake.service(self.company)

        self.assertEqual(service.company, self.company)
        self.assertEqual(service.price, Decimal("45.00"))
        self.assertEqual(service.duration_minutes, 45)
        self.assertTrue(service.is_active)

    def test_rejects_invalid_price(self):
        service = Service(
            company=self.company,
            name="Corte inválido",
            price=Decimal("0.00"),
            duration_minutes=30,
        )

        with self.assertRaises(ValidationError):
            service.full_clean()

    def test_rejects_invalid_duration(self):
        service = Service(
            company=self.company,
            name="Corte inválido",
            price=Decimal("35.00"),
            duration_minutes=0,
        )

        with self.assertRaises(ValidationError):
            service.full_clean()
