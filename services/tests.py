from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.test import APITestCase

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


class ServiceAPITests(APITestCase):
    def setUp(self):
        self.fake = FakeData()
        self.company = self.fake.company()
        self.other_company = self.fake.company()
        self.active_service = self.fake.service(self.company, name="Corte Masculino")
        self.fake.service(self.company, is_active=False, name="Barba Inativa")
        self.fake.service(self.other_company, name="Corte Outra Empresa")

    def test_lists_only_active_services_from_company_slug(self):
        url = reverse(
            "company-service-list",
            kwargs={"company_slug": self.company.slug},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(self.active_service.id))
        self.assertEqual(response.data[0]["name"], "Corte Masculino")

    def test_retrieves_active_service_from_company_slug(self):
        url = reverse(
            "company-service-detail",
            kwargs={
                "company_slug": self.company.slug,
                "service_id": self.active_service.id,
            },
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.active_service.id))

    def test_returns_not_found_for_inactive_company(self):
        inactive_company = self.fake.company(is_active=False)
        url = reverse(
            "company-service-list",
            kwargs={"company_slug": inactive_company.slug},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
