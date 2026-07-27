from datetime import time

from django.test import TestCase

from scheduling.selectors import list_available_slots
from scheduling.tests.factories import FakeData


class AvailabilitySelectorTests(TestCase):
    def setUp(self):
        self.fake = FakeData()
        self.company = self.fake.company()
        self.customer = self.fake.user()
        self.barber = self.fake.barber(self.company)
        self.service = self.fake.service(self.company, duration_minutes=30)
        self.fake.assignment(self.barber, self.service)
        self.appointment_date = self.fake.future_date()
        self.fake.working_hour(
            self.company,
            self.appointment_date,
            start_time=time(9, 0),
            end_time=time(11, 0),
        )

    def test_returns_only_available_slots(self):
        self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
            self.appointment_date,
            start_time=time(9, 30),
        )

        slots = list_available_slots(
            self.company,
            self.barber,
            self.service,
            self.appointment_date,
        )

        self.assertEqual(
            slots,
            [
                {"start_time": "09:00", "end_time": "09:30"},
                {"start_time": "10:00", "end_time": "10:30"},
                {"start_time": "10:15", "end_time": "10:45"},
                {"start_time": "10:30", "end_time": "11:00"},
            ],
        )
