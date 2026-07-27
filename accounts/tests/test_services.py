from unittest.mock import patch

from django.contrib.auth.tokens import default_token_generator
from django.test import TestCase
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.models import CustomerProfile
from accounts.services import CustomerRegistrationService, PasswordResetService
from accounts.tests.factories import FakeData


class AccountServiceTests(TestCase):
    def setUp(self):
        self.fake = FakeData()
        self.welcome_task = patch("accounts.services.send_welcome_email.delay").start()
        self.reset_task = patch(
            "accounts.services.send_password_reset_email.delay"
        ).start()
        self.addCleanup(patch.stopall)

    def test_customer_registration_service_creates_user_and_profile(self):
        with self.captureOnCommitCallbacks(execute=True):
            user = CustomerRegistrationService.register_customer(
                email=self.fake.email(),
                full_name="Cliente Serviço",
                phone="65999999999",
                password=self.fake.password(),
            )

        self.assertTrue(CustomerProfile.objects.filter(user=user).exists())
        self.assertEqual(user.phone, "65999999999")
        self.welcome_task.assert_called_once_with(str(user.id))

    def test_password_reset_request_does_not_reveal_missing_user(self):
        result = PasswordResetService.request_reset("missing@example.com")

        self.assertIsNone(result)
        self.reset_task.assert_not_called()

    def test_password_reset_confirm_updates_valid_user_password(self):
        user = self.fake.user()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        result = PasswordResetService.confirm_reset(uid, token, "NewStrong123!")

        user.refresh_from_db()
        self.assertTrue(result)
        self.assertTrue(user.check_password("NewStrong123!"))

    def test_password_reset_confirm_rejects_invalid_token(self):
        user = self.fake.user()
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        result = PasswordResetService.confirm_reset(
            uid, "invalid-token", "NewStrong123!"
        )

        self.assertFalse(result)
