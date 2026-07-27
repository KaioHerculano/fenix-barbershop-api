from datetime import time, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from scheduling.models import Appointment
from scheduling.services import (
    cancel_appointment,
    create_appointment,
    reschedule_appointment,
)
from scheduling.tests.factories import FakeData


class AppointmentServiceTests(TestCase):
    def setUp(self):
        self.fake = FakeData()
        self.cancelled_task = patch(
            "scheduling.services.send_appointment_cancelled_email.delay"
        ).start()
        self.addCleanup(patch.stopall)
        self.company = self.fake.company()
        self.customer = self.fake.user()
        self.barber = self.fake.barber(self.company)
        self.service = self.fake.service(self.company, duration_minutes=30)
        self.fake.assignment(self.barber, self.service)
        self.appointment_date = self.fake.future_date()
        self.fake.working_hour(self.company, self.appointment_date)

    def test_create_appointment_calculates_end_time(self):
        with self.captureOnCommitCallbacks(execute=True):
            appointment = create_appointment(
                self.company.slug,
                self.customer,
                {
                    "service_id": self.service.id,
                    "barber_id": self.barber.id,
                    "appointment_date": self.appointment_date,
                    "start_time": time(9, 0),
                    "notes": "Sem preferencias",
                },
            )

        self.assertEqual(appointment.end_time, time(9, 30))
        self.assertEqual(appointment.status, Appointment.Status.PENDING)

    def test_rejects_inactive_service(self):
        inactive_service = self.fake.service(self.company, is_active=False)
        self.fake.assignment(self.barber, inactive_service)

        with self.assertRaises(Exception):
            create_appointment(
                self.company.slug,
                self.customer,
                {
                    "service_id": inactive_service.id,
                    "barber_id": self.barber.id,
                    "appointment_date": self.appointment_date,
                    "start_time": time(9, 0),
                },
            )

    def test_rejects_inactive_barber(self):
        inactive_barber = self.fake.barber(self.company, is_active=False)
        self.fake.assignment(inactive_barber, self.service)

        with self.assertRaises(Exception):
            create_appointment(
                self.company.slug,
                self.customer,
                {
                    "service_id": self.service.id,
                    "barber_id": inactive_barber.id,
                    "appointment_date": self.appointment_date,
                    "start_time": time(9, 0),
                },
            )

    def test_rejects_barber_without_service_assignment(self):
        barber = self.fake.barber(self.company)

        with self.assertRaises(ValidationError):
            create_appointment(
                self.company.slug,
                self.customer,
                {
                    "service_id": self.service.id,
                    "barber_id": barber.id,
                    "appointment_date": self.appointment_date,
                    "start_time": time(9, 0),
                },
            )

    def test_rejects_appointment_in_the_past(self):
        past_date = timezone.localdate() - timedelta(days=1)
        self.fake.working_hour(self.company, past_date)

        with self.assertRaises(ValidationError):
            create_appointment(
                self.company.slug,
                self.customer,
                {
                    "service_id": self.service.id,
                    "barber_id": self.barber.id,
                    "appointment_date": past_date,
                    "start_time": time(9, 0),
                },
            )

    def test_rejects_appointment_outside_working_hours(self):
        with self.assertRaises(ValidationError):
            create_appointment(
                self.company.slug,
                self.customer,
                {
                    "service_id": self.service.id,
                    "barber_id": self.barber.id,
                    "appointment_date": self.appointment_date,
                    "start_time": time(8, 30),
                },
            )

    def test_rejects_exact_conflict(self):
        self.fake.appointment(
            self.company,
            self.fake.user(),
            self.barber,
            self.service,
            self.appointment_date,
            start_time=time(9, 0),
        )

        with self.assertRaises(ValidationError):
            create_appointment(
                self.company.slug,
                self.customer,
                {
                    "service_id": self.service.id,
                    "barber_id": self.barber.id,
                    "appointment_date": self.appointment_date,
                    "start_time": time(9, 0),
                },
            )

    def test_rejects_partial_conflict_before_existing_appointment(self):
        long_service = self.fake.service(self.company, duration_minutes=45)
        self.fake.assignment(self.barber, long_service)
        self.fake.appointment(
            self.company,
            self.fake.user(),
            self.barber,
            self.service,
            self.appointment_date,
            start_time=time(9, 30),
        )

        with self.assertRaises(ValidationError):
            create_appointment(
                self.company.slug,
                self.customer,
                {
                    "service_id": long_service.id,
                    "barber_id": self.barber.id,
                    "appointment_date": self.appointment_date,
                    "start_time": time(9, 0),
                },
            )

    def test_rejects_partial_conflict_after_existing_appointment(self):
        long_service = self.fake.service(self.company, duration_minutes=45)
        self.fake.assignment(self.barber, long_service)
        self.fake.appointment(
            self.company,
            self.fake.user(),
            self.barber,
            self.service,
            self.appointment_date,
            start_time=time(9, 0),
        )

        with self.assertRaises(ValidationError):
            create_appointment(
                self.company.slug,
                self.customer,
                {
                    "service_id": long_service.id,
                    "barber_id": self.barber.id,
                    "appointment_date": self.appointment_date,
                    "start_time": time(9, 15),
                },
            )

    def test_allows_adjacent_appointment(self):
        self.fake.appointment(
            self.company,
            self.fake.user(),
            self.barber,
            self.service,
            self.appointment_date,
            start_time=time(9, 0),
        )

        appointment = create_appointment(
            self.company.slug,
            self.customer,
            {
                "service_id": self.service.id,
                "barber_id": self.barber.id,
                "appointment_date": self.appointment_date,
                "start_time": time(9, 30),
            },
        )

        self.assertEqual(appointment.start_time, time(9, 30))

    def test_cancels_valid_appointment(self):
        appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
            self.appointment_date,
        )

        cancel_appointment(appointment)

        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Appointment.Status.CANCELLED)
        self.assertIsNotNone(appointment.cancelled_at)
        self.cancelled_task.assert_called_once_with(str(appointment.id))

    def test_rejects_repeated_cancellation(self):
        appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
            self.appointment_date,
            status=Appointment.Status.CANCELLED,
        )

        with self.assertRaises(ValidationError):
            cancel_appointment(appointment)

    def test_rejects_completed_cancellation(self):
        appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
            self.appointment_date,
            status=Appointment.Status.COMPLETED,
        )

        with self.assertRaises(ValidationError):
            cancel_appointment(appointment)

    def test_reschedules_valid_appointment(self):
        appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
            self.appointment_date,
            start_time=time(9, 0),
        )

        reschedule_appointment(
            appointment,
            {
                "appointment_date": self.appointment_date,
                "start_time": time(10, 0),
            },
        )

        appointment.refresh_from_db()
        self.assertEqual(appointment.start_time, time(10, 0))
        self.assertEqual(appointment.end_time, time(10, 30))

    def test_rejects_cancelled_reschedule(self):
        appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
            self.appointment_date,
            status=Appointment.Status.CANCELLED,
        )

        with self.assertRaises(ValidationError):
            reschedule_appointment(
                appointment,
                {
                    "appointment_date": self.appointment_date,
                    "start_time": time(10, 0),
                },
            )

    def test_rejects_completed_reschedule(self):
        appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
            self.appointment_date,
            status=Appointment.Status.COMPLETED,
        )

        with self.assertRaises(ValidationError):
            reschedule_appointment(
                appointment,
                {
                    "appointment_date": self.appointment_date,
                    "start_time": time(10, 0),
                },
            )

    def test_rejects_reschedule_to_unavailable_time(self):
        appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
            self.appointment_date,
            start_time=time(9, 0),
        )
        self.fake.appointment(
            self.company,
            self.fake.user(),
            self.barber,
            self.service,
            self.appointment_date,
            start_time=time(10, 0),
        )

        with self.assertRaises(ValidationError):
            reschedule_appointment(
                appointment,
                {
                    "appointment_date": self.appointment_date,
                    "start_time": time(10, 0),
                },
            )
