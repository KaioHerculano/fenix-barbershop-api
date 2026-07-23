from unittest.mock import patch

from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import CustomerProfile, User
from accounts.services import CustomerRegistrationService, PasswordResetService
from accounts.validators import ComplexPasswordValidator
from company.models import Company, CompanyEmployee


class FakeData:
    def email(self):
        return f"{get_random_string(10).lower()}@example.com"

    def password(self):
        return "StrongPass123!"

    def user(self, full_name=None):
        value = get_random_string(8)
        return User.objects.create_user(
            email=self.email(),
            full_name=full_name or f"Pessoa {value}",
            password=self.password(),
        )

    def owner_payload(self):
        value = get_random_string(8).lower()
        return {
            "company_name": f"Barbearia {value}",
            "company_slug": f"barbearia-{value}",
            "full_name": f"Owner {value}",
            "email": self.email(),
            "password": self.password(),
        }

    def customer_payload(self):
        value = get_random_string(8)
        return {
            "full_name": f"Cliente {value}",
            "email": self.email(),
            "phone": "65999999999",
            "password": self.password(),
            "password_confirmation": self.password(),
        }


class UserModelTests(TestCase):
    def setUp(self):
        self.fake = FakeData()

    def test_create_user_with_email_login(self):
        user = self.fake.user(full_name="Cliente Teste")

        self.assertEqual(str(user), user.email)
        self.assertEqual(user.full_name, "Cliente Teste")
        self.assertTrue(user.check_password(self.fake.password()))

    def test_create_user_requires_email(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email="",
                full_name="Sem Email",
                password=self.fake.password(),
            )

    def test_create_superuser_requires_staff_and_superuser_flags(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email=self.fake.email(),
                full_name="Admin",
                password=self.fake.password(),
                is_staff=False,
            )

        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email=self.fake.email(),
                full_name="Admin",
                password=self.fake.password(),
                is_superuser=False,
            )

    def test_customer_profile_string_representation(self):
        user = self.fake.user()
        profile = CustomerProfile.objects.create(user=user)

        self.assertEqual(str(profile), f"Profile: {user.email}")


class ComplexPasswordValidatorTests(TestCase):
    def setUp(self):
        self.validator = ComplexPasswordValidator()

    def test_accepts_complex_password(self):
        self.validator.validate("StrongPass123!")

    def test_rejects_password_without_uppercase(self):
        with self.assertRaises(ValidationError):
            self.validator.validate("strongpass123!")

    def test_rejects_password_without_lowercase(self):
        with self.assertRaises(ValidationError):
            self.validator.validate("STRONGPASS123!")

    def test_rejects_password_without_number(self):
        with self.assertRaises(ValidationError):
            self.validator.validate("StrongPassword!")

    def test_rejects_password_without_symbol(self):
        with self.assertRaises(ValidationError):
            self.validator.validate("StrongPass123")

    def test_returns_help_text(self):
        self.assertIn("maiúscula", self.validator.get_help_text())


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


class AccountAPITests(APITestCase):
    def setUp(self):
        self.fake = FakeData()
        self.welcome_task = patch("accounts.services.send_welcome_email.delay").start()
        self.reset_task = patch(
            "accounts.services.send_password_reset_email.delay"
        ).start()
        self.addCleanup(patch.stopall)

    def test_owner_registration_creates_company_and_owner_link(self):
        payload = self.fake.owner_payload()
        url = reverse("owner_registration")

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(url, payload, format="json")

        user = User.objects.get(email=payload["email"])
        company = Company.objects.get(slug=payload["company_slug"])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            CompanyEmployee.objects.filter(
                user=user,
                company=company,
                role=User.Role.OWNER,
            ).exists()
        )

    def test_owner_registration_rejects_duplicate_email(self):
        user = self.fake.user()
        payload = self.fake.owner_payload()
        payload["email"] = user.email
        url = reverse("owner_registration")

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_owner_registration_rejects_duplicate_company_slug(self):
        company = Company.objects.create(name="Fenix", slug="fenix")
        payload = self.fake.owner_payload()
        payload["company_slug"] = company.slug
        url = reverse("owner_registration")

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_customer_registration_creates_customer_profile(self):
        payload = self.fake.customer_payload()
        url = reverse("customer_registration")

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(url, payload, format="json")

        user = User.objects.get(email=payload["email"])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CustomerProfile.objects.filter(user=user).exists())
        self.welcome_task.assert_called_once_with(str(user.id))

    def test_customer_registration_rejects_password_mismatch(self):
        payload = self.fake.customer_payload()
        payload["password_confirmation"] = "DifferentPass123!"
        url = reverse("customer_registration")

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_me_requires_authentication(self):
        response = self.client.get(reverse("user_me"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_me_returns_authenticated_user(self):
        user = self.fake.user(full_name="Cliente Logado")
        self.client.force_authenticate(user=user)

        response = self.client.get(reverse("user_me"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], user.email)
        self.assertNotIn("password", response.data)

    def test_user_me_updates_allowed_fields(self):
        user = self.fake.user()
        self.client.force_authenticate(user=user)

        response = self.client.patch(
            reverse("user_me"),
            {"full_name": "Nome Atualizado", "phone": "65988888888"},
            format="json",
        )

        user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(user.full_name, "Nome Atualizado")
        self.assertEqual(user.phone, "65988888888")

    def test_password_reset_request_accepts_valid_email(self):
        user = self.fake.user()

        response = self.client.post(
            reverse("password_reset_request"),
            {"email": user.email},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.reset_task.assert_called_once()

    def test_password_reset_request_rejects_invalid_email(self):
        response = self.client.post(
            reverse("password_reset_request"),
            {"email": "invalid"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_confirm_updates_password(self):
        user = self.fake.user()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        response = self.client.post(
            reverse("password_reset_confirm"),
            {
                "uidb64": uid,
                "token": token,
                "new_password": "NewStrong123!",
                "new_password_confirmation": "NewStrong123!",
            },
            format="json",
        )

        user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(user.check_password("NewStrong123!"))

    def test_password_reset_confirm_rejects_invalid_token(self):
        user = self.fake.user()
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        response = self.client.post(
            reverse("password_reset_confirm"),
            {
                "uidb64": uid,
                "token": "invalid-token",
                "new_password": "NewStrong123!",
                "new_password_confirmation": "NewStrong123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_confirm_rejects_password_mismatch(self):
        response = self.client.post(
            reverse("password_reset_confirm"),
            {
                "uidb64": "invalid",
                "token": "invalid",
                "new_password": "NewStrong123!",
                "new_password_confirmation": "OtherStrong123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
