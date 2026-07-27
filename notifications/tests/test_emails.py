from django.test import TestCase, override_settings

from notifications import emails
from notifications.tests.factories import FakeData


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
