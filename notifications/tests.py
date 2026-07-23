import json
from datetime import timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from django.utils import timezone
from django.utils.crypto import get_random_string

from accounts.models import User
from company.models import Company, CompanyEmployee, StaffInvitation
from notifications import emails
from notifications.services import resend_payload, send_email
from notifications.tasks import (
    send_appointment_cancelled_email,
    send_appointment_confirmation_email,
    send_password_reset_email,
    send_staff_invitation_email,
    send_welcome_email,
)
from scheduling.models import Appointment
from services.models import Service


class FakeData:
    def email(self):
        return f"{get_random_string(10).lower()}@example.com"

    def user(self):
        return User.objects.create_user(
            email=self.email(),
            full_name="Cliente Email",
            password="StrongPass123!",
        )

    def company(self):
        value = get_random_string(8).lower()
        return Company.objects.create(name=f"Barbearia {value}", slug=value)

    def service(self, company):
        return Service.objects.create(
            company=company,
            name="Corte",
            price=Decimal("45.00"),
            duration_minutes=30,
            is_active=True,
        )

    def barber(self, company):
        return CompanyEmployee.objects.create(
            user=self.user(),
            company=company,
            role=User.Role.BARBER,
            is_active=True,
        )

    def appointment(self):
        company = self.company()
        return Appointment.objects.create(
            company=company,
            customer=self.user(),
            barber=self.barber(company),
            service=self.service(company),
            appointment_date=timezone.localdate(),
            start_time=timezone.datetime(2026, 1, 1, 9, 0).time(),
            end_time=timezone.datetime(2026, 1, 1, 9, 30).time(),
            status=Appointment.Status.CONFIRMED,
        )

    def invitation(self):
        token, digest = StaffInvitation.build_token()
        company = self.company()
        return (
            StaffInvitation.objects.create(
                company=company,
                email=self.email(),
                role=User.Role.BARBER,
                invited_by=self.user(),
                token_digest=digest,
                expires_at=timezone.now() + timedelta(days=7),
            ),
            token,
        )


class EmailBuilderTests(TestCase):
    def setUp(self):
        self.fake = FakeData()

    @override_settings(ROOT_URLCONF="app.urls")
    def test_builds_welcome_email(self):
        user = self.fake.user()

        message = emails.welcome_email(user)

        self.assertEqual(message["to"], user.email)
        self.assertIn("Fenix", message["subject"])
        self.assertIn(user.full_name, message["html"])

    def test_builds_password_reset_email_with_link(self):
        user = self.fake.user()

        message = emails.password_reset_email(user, "uid", "token")

        self.assertIn("uid=uid", message["html"])
        self.assertIn("token=token", message["text"])

    def test_builds_appointment_emails(self):
        appointment = self.fake.appointment()

        confirmation = emails.appointment_confirmation_email(appointment)
        cancelled = emails.appointment_cancelled_email(appointment)

        self.assertIn(appointment.service.name, confirmation["html"])
        self.assertIn(appointment.service.name, cancelled["html"])

    def test_builds_staff_invitation_email(self):
        invitation, token = self.fake.invitation()

        message = emails.staff_invitation_email(invitation, token)

        self.assertIn(token, message["html"])
        self.assertEqual(message["to"], invitation.email)


class ResendServiceTests(TestCase):
    def test_resend_payload_uses_expected_shape(self):
        payload = resend_payload(
            {
                "to": "user@example.com",
                "subject": "Subject",
                "html": "<p>Hello</p>",
                "text": "Hello",
            }
        )

        self.assertEqual(payload["to"], ["user@example.com"])
        self.assertEqual(payload["subject"], "Subject")

    @patch.dict("os.environ", {}, clear=True)
    def test_send_email_skips_without_api_key(self):
        result = send_email(
            {
                "to": "user@example.com",
                "subject": "Subject",
                "html": "<p>Hello</p>",
                "text": "Hello",
            }
        )

        self.assertFalse(result["sent"])
        self.assertEqual(result["reason"], "missing_api_key")

    @patch.dict("os.environ", {"RESEND_API_KEY": "secret"}, clear=True)
    @patch("notifications.services.urlopen")
    def test_send_email_posts_to_resend(self, urlopen_mock):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(
            {"id": "email-id"}
        ).encode("utf-8")
        urlopen_mock.return_value = response

        result = send_email(
            {
                "to": "user@example.com",
                "subject": "Subject",
                "html": "<p>Hello</p>",
                "text": "Hello",
            }
        )

        self.assertEqual(result["id"], "email-id")


class NotificationTaskTests(TestCase):
    def setUp(self):
        self.fake = FakeData()

    @patch("notifications.tasks.send_email")
    def test_send_welcome_email_task(self, send_email_mock):
        user = self.fake.user()

        send_welcome_email.run(str(user.id))

        send_email_mock.assert_called_once()

    @patch("notifications.tasks.send_email")
    def test_send_password_reset_email_task(self, send_email_mock):
        user = self.fake.user()

        send_password_reset_email.run(str(user.id), "uid", "token")

        send_email_mock.assert_called_once()

    @patch("notifications.tasks.send_email")
    def test_send_appointment_confirmation_task(self, send_email_mock):
        appointment = self.fake.appointment()

        send_appointment_confirmation_email.run(str(appointment.id))

        send_email_mock.assert_called_once()

    @patch("notifications.tasks.send_email")
    def test_send_appointment_cancelled_task(self, send_email_mock):
        appointment = self.fake.appointment()

        send_appointment_cancelled_email.run(str(appointment.id))

        send_email_mock.assert_called_once()

    @patch("notifications.tasks.send_email")
    def test_send_staff_invitation_task(self, send_email_mock):
        invitation, token = self.fake.invitation()

        send_staff_invitation_email.run(str(invitation.id), token)

        send_email_mock.assert_called_once()
