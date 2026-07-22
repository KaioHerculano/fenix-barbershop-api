from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from barbers.models import BarberService
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


class BarberServiceModelTests(TestCase):
    def setUp(self):
        self.fake = FakeData()
        self.company = self.fake.company()

    def test_create_valid_barber_service_assignment(self):
        barber = self.fake.employee(self.company)
        service = self.fake.service(self.company)

        assignment = BarberService.objects.create(barber=barber, service=service)

        self.assertEqual(assignment.barber, barber)
        self.assertEqual(assignment.service, service)
        self.assertTrue(assignment.is_active)

    def test_rejects_assignment_for_non_barber_employee(self):
        owner = self.fake.employee(self.company, role=User.Role.OWNER)
        service = self.fake.service(self.company)

        assignment = BarberService(barber=owner, service=service)

        with self.assertRaises(ValidationError):
            assignment.full_clean()

    def test_rejects_assignment_between_different_companies(self):
        barber = self.fake.employee(self.company)
        other_company = self.fake.company()
        service = self.fake.service(other_company)

        assignment = BarberService(barber=barber, service=service)

        with self.assertRaises(ValidationError):
            assignment.full_clean()


class BarberAPITests(APITestCase):
    def setUp(self):
        self.fake = FakeData()
        self.company = self.fake.company()
        self.other_company = self.fake.company()
        self.barber = self.fake.employee(
            self.company,
            user=self.fake.user(full_name="Carlos Navalha"),
        )
        self.inactive_barber = self.fake.employee(self.company, is_active=False)
        self.owner = self.fake.employee(self.company, role=User.Role.OWNER)
        self.customer = self.fake.employee(self.company, role=User.Role.CUSTOMER)
        self.other_barber = self.fake.employee(self.other_company)
        self.service = self.fake.service(self.company)
        self.inactive_service = self.fake.service(self.company, is_active=False)
        self.other_service = self.fake.service(self.other_company)
        BarberService.objects.create(barber=self.barber, service=self.service)
        BarberService.objects.create(
            barber=self.barber,
            service=self.inactive_service,
        )
        BarberService.objects.create(
            barber=self.other_barber,
            service=self.other_service,
        )

    def test_lists_only_active_barbers_from_company_slug(self):
        url = reverse(
            "company-barber-list",
            kwargs={"company_slug": self.company.slug},
        )

        response = self.client.get(url)

        ids = {item["id"] for item in response.data}
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ids, {str(self.barber.id)})
        self.assertNotIn("email", response.data[0])

    def test_retrieves_active_barber(self):
        url = reverse(
            "company-barber-detail",
            kwargs={
                "company_slug": self.company.slug,
                "barber_id": self.barber.id,
            },
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.barber.id))
        self.assertEqual(response.data["full_name"], "Carlos Navalha")

    def test_lists_only_active_services_from_barber(self):
        url = reverse(
            "company-barber-service-list",
            kwargs={
                "company_slug": self.company.slug,
                "barber_id": self.barber.id,
            },
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(self.service.id))

    def test_returns_not_found_for_unknown_company_slug(self):
        url = reverse(
            "company-barber-list",
            kwargs={"company_slug": "empresa-inexistente"},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
