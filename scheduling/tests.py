from datetime import time

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.test import APITestCase

from company.models import Company
from scheduling.models import WorkingHour


class FakeData:
    def company(self, is_active=True):
        value = get_random_string(8).lower()
        return Company.objects.create(
            name=f"Barbearia {value}",
            slug=f"barbearia-{value}",
            is_active=is_active,
        )

    def working_hour(self, company, is_active=True):
        return WorkingHour.objects.create(
            company=company,
            weekday=WorkingHour.Weekday.MONDAY,
            start_time=time(9, 0),
            end_time=time(18, 0),
            is_active=is_active,
        )


class WorkingHourModelTests(TestCase):
    def setUp(self):
        self.fake = FakeData()
        self.company = self.fake.company()

    def test_create_valid_working_hour(self):
        working_hour = self.fake.working_hour(self.company)

        self.assertEqual(working_hour.company, self.company)
        self.assertEqual(working_hour.weekday, WorkingHour.Weekday.MONDAY)
        self.assertTrue(working_hour.is_active)

    def test_rejects_start_time_equal_to_end_time(self):
        working_hour = WorkingHour(
            company=self.company,
            weekday=WorkingHour.Weekday.TUESDAY,
            start_time=time(10, 0),
            end_time=time(10, 0),
        )

        with self.assertRaises(ValidationError):
            working_hour.full_clean()

    def test_rejects_start_time_after_end_time(self):
        working_hour = WorkingHour(
            company=self.company,
            weekday=WorkingHour.Weekday.TUESDAY,
            start_time=time(18, 0),
            end_time=time(10, 0),
        )

        with self.assertRaises(ValidationError):
            working_hour.full_clean()


class WorkingHourAPITests(APITestCase):
    def setUp(self):
        self.fake = FakeData()
        self.company = self.fake.company()
        self.other_company = self.fake.company()
        self.working_hour = self.fake.working_hour(self.company)
        self.fake.working_hour(self.company, is_active=False)
        self.fake.working_hour(self.other_company)

    def test_lists_only_active_working_hours_from_company_slug(self):
        url = reverse(
            "company-working-hour-list",
            kwargs={"company_slug": self.company.slug},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(self.working_hour.id))

    def test_returns_not_found_for_inactive_company(self):
        inactive_company = self.fake.company(is_active=False)
        url = reverse(
            "company-working-hour-list",
            kwargs={"company_slug": inactive_company.slug},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
