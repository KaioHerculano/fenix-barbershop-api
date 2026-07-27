from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from services.tests.factories import FakeData


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
