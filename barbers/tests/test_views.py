from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from barbers.models import BarberService
from barbers.tests.factories import FakeData


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
