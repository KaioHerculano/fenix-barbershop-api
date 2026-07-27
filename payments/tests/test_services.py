from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from payments.models import Payment, PaymentWebhookEvent
from payments.services import create_payment_for_appointment, process_payment_webhook
from payments.tests.factories import FakeData
from scheduling.models import Appointment


class PaymentServiceTests(TestCase):
    def setUp(self):
        self.fake = FakeData()
        self.company = self.fake.company()
        self.customer = self.fake.user()
        self.other_customer = self.fake.user()
        self.barber = self.fake.barber(self.company)
        self.service = self.fake.service(self.company, price=Decimal("75.90"))
        self.fake.assignment(self.barber, self.service)
        self.appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
        )

    def test_creates_payment_using_service_price(self):
        payment, created = create_payment_for_appointment(
            self.customer,
            self.appointment.id,
            "payment-create-key",
        )

        self.assertTrue(created)
        self.assertEqual(payment.amount, Decimal("75.90"))
        self.assertEqual(payment.appointment, self.appointment)
        self.assertEqual(payment.provider, Payment.Provider.INTERNAL)
        self.assertEqual(payment.payment_method, Payment.Method.PIX)
        self.assertTrue(payment.provider_payment_id.startswith("internal-"))
        self.assertTrue(payment.payment_code)

    def test_returns_same_payment_for_same_idempotency_key(self):
        first_payment, first_created = create_payment_for_appointment(
            self.customer,
            self.appointment.id,
            "payment-same-key",
        )
        second_payment, second_created = create_payment_for_appointment(
            self.customer,
            self.appointment.id,
            "payment-same-key",
        )

        self.assertTrue(first_created)
        self.assertFalse(second_created)
        self.assertEqual(second_payment.id, first_payment.id)
        self.assertEqual(Payment.objects.count(), 1)

    def test_returns_existing_pending_payment_for_same_appointment(self):
        first_payment, first_created = create_payment_for_appointment(
            self.customer,
            self.appointment.id,
            "payment-first-key",
        )
        second_payment, second_created = create_payment_for_appointment(
            self.customer,
            self.appointment.id,
            "payment-second-key",
        )

        self.assertTrue(first_created)
        self.assertFalse(second_created)
        self.assertEqual(second_payment.id, first_payment.id)
        self.assertEqual(Payment.objects.count(), 1)

    def test_rejects_idempotency_key_from_other_user(self):
        create_payment_for_appointment(
            self.customer,
            self.appointment.id,
            "payment-private-key",
        )

        with self.assertRaises(ValidationError):
            create_payment_for_appointment(
                self.other_customer,
                self.appointment.id,
                "payment-private-key",
            )

    def test_rejects_cancelled_appointment(self):
        appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
            status=Appointment.Status.CANCELLED,
        )

        with self.assertRaises(ValidationError):
            create_payment_for_appointment(
                self.customer,
                appointment.id,
                "payment-cancelled-appointment",
            )

    def test_rejects_completed_appointment(self):
        appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
            status=Appointment.Status.COMPLETED,
        )

        with self.assertRaises(ValidationError):
            create_payment_for_appointment(
                self.customer,
                appointment.id,
                "payment-completed-appointment",
            )

    def test_rejects_appointment_with_paid_payment(self):
        Payment.objects.create(
            user=self.customer,
            appointment=self.appointment,
            amount=self.service.price,
            status=Payment.Status.PAID,
            idempotency_key="payment-paid-key",
            paid_at=timezone.now(),
        )

        with self.assertRaises(ValidationError):
            create_payment_for_appointment(
                self.customer,
                self.appointment.id,
                "payment-after-paid-key",
            )

    def test_processes_paid_webhook_once_and_confirms_appointment(self):
        payment, _ = create_payment_for_appointment(
            self.customer,
            self.appointment.id,
            "payment-webhook-key",
        )

        with self.captureOnCommitCallbacks(execute=True):
            event, processed = process_payment_webhook(
                {
                    "id": "event-1",
                    "provider_payment_id": payment.provider_payment_id,
                    "status": "paid",
                    "type": "payment",
                    "action": "payment.updated",
                },
                provider=Payment.Provider.INTERNAL,
            )

        payment.refresh_from_db()
        self.appointment.refresh_from_db()
        self.assertTrue(processed)
        self.assertEqual(event.processed_at.date(), timezone.localdate())
        self.assertEqual(payment.status, Payment.Status.PAID)
        self.assertIsNotNone(payment.paid_at)
        self.assertEqual(self.appointment.status, Appointment.Status.CONFIRMED)

    def test_ignores_repeated_webhook_event(self):
        payment, _ = create_payment_for_appointment(
            self.customer,
            self.appointment.id,
            "payment-duplicated-webhook-key",
        )
        payload = {
            "id": "event-duplicated",
            "provider_payment_id": payment.provider_payment_id,
            "status": "paid",
            "type": "payment",
            "action": "payment.updated",
        }

        process_payment_webhook(payload, provider=Payment.Provider.INTERNAL)
        event, processed = process_payment_webhook(
            payload,
            provider=Payment.Provider.INTERNAL,
        )

        self.assertFalse(processed)
        self.assertEqual(PaymentWebhookEvent.objects.count(), 1)
        self.assertIsNotNone(event.processed_at)
