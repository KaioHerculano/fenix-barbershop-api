from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.validators import ComplexPasswordValidator


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
