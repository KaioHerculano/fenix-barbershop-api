from django.test import TestCase

from accounts.models import CustomerProfile, User
from accounts.tests.factories import FakeData


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
