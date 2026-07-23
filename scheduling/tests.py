from datetime import date, time, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase

from accounts.models import User
from barbers.models import BarberService
from company.models import Company, CompanyEmployee
from scheduling.models import Appointment, WorkingHour
from scheduling.selectors import list_available_slots
from scheduling.services import (
    cancel_appointment,
    create_appointment,
    reschedule_appointment,
)
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

    def barber(self, company, is_active=True, user=None):
        return CompanyEmployee.objects.create(
            user=user or self.user(),
            company=company,
            role=User.Role.BARBER,
            is_active=is_active,
        )

    def owner(self, company):
        return CompanyEmployee.objects.create(
            user=self.user(),
            company=company,
            role=User.Role.OWNER,
            is_active=True,
        )

    def service(self, company, duration_minutes=30, is_active=True):
        value = get_random_string(8)
        return Service.objects.create(
            company=company,
            name=f"Servico {value}",
            price=Decimal("50.00"),
            duration_minutes=duration_minutes,
            is_active=is_active,
        )

    def assignment(self, barber, service, is_active=True):
        return BarberService.objects.create(
            barber=barber,
            service=service,
            is_active=is_active,
        )

    def future_date(self, days_ahead=1):
        return timezone.localdate() + timedelta(days=days_ahead)

    def working_hour(
        self,
        company,
        appointment_date=None,
        start_time=time(9, 0),
        end_time=time(11, 0),
        is_active=True,
    ):
        value = appointment_date or self.future_date()
        return WorkingHour.objects.create(
            company=company,
            weekday=value.weekday(),
            start_time=start_time,
            end_time=end_time,
            is_active=is_active,
        )

    def appointment(
        self,
        company,
        customer,
        barber,
        service,
        appointment_date,
        start_time=time(9, 0),
        status=Appointment.Status.CONFIRMED,
    ):
        start_dt = timezone.datetime.combine(date.today(), start_time)
        end_time = (start_dt + timedelta(minutes=service.duration_minutes)).time()
        return Appointment.objects.create(
            company=company,
            customer=customer,
            barber=barber,
            service=service,
            appointment_date=appointment_date,
            start_time=start_time,
            end_time=end_time,
            status=status,
        )


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


class AppointmentServiceTests(TestCase):
    def setUp(self):
        self.fake = FakeData()
        self.confirmation_task = patch(
            "scheduling.services.send_appointment_confirmation_email.delay"
        ).start()
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
        self.assertEqual(appointment.status, Appointment.Status.CONFIRMED)
        self.confirmation_task.assert_called_once_with(str(appointment.id))

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


class WorkingHourAPITests(APITestCase):
    def setUp(self):
        self.fake = FakeData()
        self.company = self.fake.company()
        self.other_company = self.fake.company()
        self.appointment_date = self.fake.future_date()
        self.working_hour = self.fake.working_hour(self.company, self.appointment_date)
        self.fake.working_hour(self.company, self.appointment_date, is_active=False)
        self.fake.working_hour(self.other_company, self.appointment_date)

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


class AppointmentAPITests(APITestCase):
    def setUp(self):
        self.fake = FakeData()
        self.confirmation_task = patch(
            "scheduling.services.send_appointment_confirmation_email.delay"
        ).start()
        self.cancelled_task = patch(
            "scheduling.services.send_appointment_cancelled_email.delay"
        ).start()
        self.addCleanup(patch.stopall)
        self.company = self.fake.company()
        self.customer = self.fake.user(full_name="Cliente Agenda")
        self.other_customer = self.fake.user()
        self.barber = self.fake.barber(self.company)
        self.service = self.fake.service(self.company, duration_minutes=30)
        self.fake.assignment(self.barber, self.service)
        self.appointment_date = self.fake.future_date()
        self.fake.working_hour(self.company, self.appointment_date)

    def availability_url(self):
        return reverse(
            "company-appointment-availability",
            kwargs={"company_slug": self.company.slug},
        )

    def appointments_url(self):
        return reverse(
            "company-appointment-list-create",
            kwargs={"company_slug": self.company.slug},
        )

    def detail_url(self, appointment):
        return reverse(
            "company-appointment-detail",
            kwargs={
                "company_slug": self.company.slug,
                "appointment_id": appointment.id,
            },
        )

    def cancel_url(self, appointment):
        return reverse(
            "company-appointment-cancel",
            kwargs={
                "company_slug": self.company.slug,
                "appointment_id": appointment.id,
            },
        )

    def reschedule_url(self, appointment):
        return reverse(
            "company-appointment-reschedule",
            kwargs={
                "company_slug": self.company.slug,
                "appointment_id": appointment.id,
            },
        )

    def test_availability_returns_available_slots(self):
        response = self.client.get(
            self.availability_url(),
            {
                "date": self.appointment_date.isoformat(),
                "barber_id": self.barber.id,
                "service_id": self.service.id,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn({"start_time": "09:00", "end_time": "09:30"}, response.data)

    def test_availability_rejects_missing_params(self):
        response = self.client.get(self.availability_url())

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_availability_returns_not_found_for_unknown_service(self):
        response = self.client.get(
            self.availability_url(),
            {
                "date": self.appointment_date.isoformat(),
                "barber_id": self.barber.id,
                "service_id": self.fake.company().id,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_requires_authentication_to_create_appointment(self):
        response = self.client.post(self.appointments_url(), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_creates_appointment(self):
        self.client.force_authenticate(user=self.customer)

        response = self.client.post(
            self.appointments_url(),
            {
                "service_id": str(self.service.id),
                "barber_id": str(self.barber.id),
                "appointment_date": self.appointment_date.isoformat(),
                "start_time": "09:00",
                "notes": "Sem preferencias",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], Appointment.Status.CONFIRMED)
        self.assertEqual(response.data["end_time"], "09:30:00")
        self.assertNotIn("customer", response.data)

    def test_user_lists_only_own_appointments(self):
        own_appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
            self.appointment_date,
        )
        self.fake.appointment(
            self.company,
            self.other_customer,
            self.barber,
            self.service,
            self.appointment_date,
            start_time=time(10, 0),
        )
        self.client.force_authenticate(user=self.customer)

        response = self.client.get(self.appointments_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(own_appointment.id))

    def test_user_retrieves_own_appointment(self):
        appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
            self.appointment_date,
        )
        self.client.force_authenticate(user=self.customer)

        response = self.client.get(self.detail_url(appointment))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(appointment.id))

    def test_user_cannot_retrieve_other_customer_appointment(self):
        appointment = self.fake.appointment(
            self.company,
            self.other_customer,
            self.barber,
            self.service,
            self.appointment_date,
        )
        self.client.force_authenticate(user=self.customer)

        response = self.client.get(self.detail_url(appointment))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cancels_own_appointment(self):
        appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
            self.appointment_date,
        )
        self.client.force_authenticate(user=self.customer)

        response = self.client.patch(self.cancel_url(appointment), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Appointment.Status.CANCELLED)

    def test_user_cannot_cancel_other_customer_appointment(self):
        appointment = self.fake.appointment(
            self.company,
            self.other_customer,
            self.barber,
            self.service,
            self.appointment_date,
        )
        self.client.force_authenticate(user=self.customer)

        response = self.client.patch(self.cancel_url(appointment), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_reschedules_own_appointment(self):
        appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
            self.appointment_date,
            start_time=time(9, 0),
        )
        self.client.force_authenticate(user=self.customer)

        response = self.client.patch(
            self.reschedule_url(appointment),
            {
                "appointment_date": self.appointment_date.isoformat(),
                "start_time": "10:00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["start_time"], "10:00:00")

    def test_user_cannot_reschedule_other_customer_appointment(self):
        appointment = self.fake.appointment(
            self.company,
            self.other_customer,
            self.barber,
            self.service,
            self.appointment_date,
        )
        self.client.force_authenticate(user=self.customer)

        response = self.client.patch(
            self.reschedule_url(appointment),
            {
                "appointment_date": self.appointment_date.isoformat(),
                "start_time": "10:00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
