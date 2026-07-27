from unittest.mock import patch

from django.test import TestCase

from notifications.tasks import (
    send_appointment_cancelled_email,
    send_appointment_confirmation_email,
    send_password_reset_email,
    send_staff_invitation_email,
    send_welcome_email,
)
from notifications.tests.factories import FakeData


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
