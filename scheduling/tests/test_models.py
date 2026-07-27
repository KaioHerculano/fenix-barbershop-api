from datetime import time

from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase

from scheduling.models import WorkingHour
from scheduling.tests.factories import FakeData


class WorkingHourModelTests(TestCase):
    def setUp(self):
        self.fake = FakeData()
        self.company = self.fake.company()

    def test_create_valid_working_hour(self):
        working_hour = self.fake.working_hour(self.company)

        self.assertEqual(working_hour.company, self.company)
        self.assertEqual(working_hour.weekday, self.fake.future_date().weekday())
        self.assertTrue(working_hour.is_active)

    def test_rejects_start_time_equal_to_end_time(self):
        working_hour = WorkingHour(
            company=self.company,
            weekday=WorkingHour.Weekday.TUESDAY,
            start_time=time(10, 0),
            end_time=time(10, 0),
        )

        with self.assertRaises(DjangoValidationError):
            working_hour.full_clean()

    def test_rejects_start_time_after_end_time(self):
        working_hour = WorkingHour(
            company=self.company,
            weekday=WorkingHour.Weekday.TUESDAY,
            start_time=time(18, 0),
            end_time=time(10, 0),
        )

        with self.assertRaises(DjangoValidationError):
            working_hour.full_clean()
