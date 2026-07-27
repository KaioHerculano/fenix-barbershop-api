from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase

from payments.models import Payment
from payments.tests.factories import FakeData


class PaymentModelTests(TestCase):
    def setUp(self):
        self.fake = FakeData()
        self.company = self.fake.company()
        self.customer = self.fake.user()
        self.barber = self.fake.barber(self.company)
        self.service = self.fake.service(self.company)
        self.fake.assignment(self.barber, self.service)
        self.appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
        )

    def test_creates_valid_payment(self):
        payment = Payment.objects.create(
            user=self.customer,
            appointment=self.appointment,
            amount=self.service.price,
            idempotency_key="payment-valid-key",
        )

        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertEqual(payment.provider, Payment.Provider.INTERNAL)
        self.assertEqual(payment.amount, Decimal("50.00"))

    def test_rejects_invalid_amount(self):
        payment = Payment(
            user=self.customer,
            appointment=self.appointment,
            amount=Decimal("0.00"),
            idempotency_key="payment-invalid-amount",
        )

        with self.assertRaises(DjangoValidationError):
            payment.full_clean()

    def test_rejects_payment_for_other_customer_appointment(self):
        other_user = self.fake.user()
        payment = Payment(
            user=other_user,
            appointment=self.appointment,
            amount=self.service.price,
            idempotency_key="payment-other-customer",
        )

        with self.assertRaises(DjangoValidationError):
            payment.full_clean()
