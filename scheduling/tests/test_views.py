from datetime import time
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from scheduling.models import Appointment
from scheduling.tests.factories import FakeData


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
        self.assertEqual(response.data["status"], Appointment.Status.PENDING)
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
