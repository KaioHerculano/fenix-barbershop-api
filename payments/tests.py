import hashlib
import hmac
import json
from datetime import time, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase

from accounts.models import User
from barbers.models import BarberService
from company.models import Company, CompanyEmployee
from payments.gateways.base import PixChargeRequest
from payments.gateways.mercado_pago import MercadoPagoPaymentGateway
from payments.models import Payment, PaymentWebhookEvent
from payments.services import create_payment_for_appointment, process_payment_webhook
from scheduling.models import Appointment
from services.models import Service


class FakeData:
    def company(self, is_active=True):
        value = get_random_string(8).lower()
        return Company.objects.create(
            name=f"Barbearia {value}",
            slug=f"barbearia-{value}",
            is_active=is_active,
        )

    def user(self, full_name=None, is_active=True):
        value = get_random_string(10).lower()
        return User.objects.create_user(
            email=f"{value}@example.com",
            full_name=full_name or f"Pessoa {value}",
            password="StrongPass123!",
            is_active=is_active,
        )

    def barber(self, company):
        return CompanyEmployee.objects.create(
            user=self.user(),
            company=company,
            role=User.Role.BARBER,
            is_active=True,
        )

    def service(self, company, price=Decimal("50.00")):
        value = get_random_string(8)
        return Service.objects.create(
            company=company,
            name=f"Servico {value}",
            price=price,
            duration_minutes=30,
            is_active=True,
        )

    def assignment(self, barber, service):
        return BarberService.objects.create(
            barber=barber,
            service=service,
            is_active=True,
        )

    def appointment(
        self,
        company,
        customer,
        barber,
        service,
        status=Appointment.Status.CONFIRMED,
    ):
        appointment_date = timezone.localdate() + timedelta(days=1)
        return Appointment.objects.create(
            company=company,
            customer=customer,
            barber=barber,
            service=service,
            appointment_date=appointment_date,
            start_time=time(9, 0),
            end_time=time(9, 30),
            status=status,
        )


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


class PaymentAPITests(APITestCase):
    def setUp(self):
        self.fake = FakeData()
        self.company = self.fake.company()
        self.customer = self.fake.user()
        self.other_customer = self.fake.user()
        self.barber = self.fake.barber(self.company)
        self.service = self.fake.service(self.company)
        self.fake.assignment(self.barber, self.service)
        self.appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
        )

    def create_url(self):
        return reverse("payment-create")

    def detail_url(self, payment):
        return reverse("payment-detail", kwargs={"payment_id": payment.id})

    def test_requires_authentication_to_create_payment(self):
        response = self.client.post(self.create_url(), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_creates_payment(self):
        self.client.force_authenticate(user=self.customer)

        response = self.client.post(
            self.create_url(),
            {"appointment_id": str(self.appointment.id)},
            HTTP_IDEMPOTENCY_KEY="api-payment-key",
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["appointment_id"], str(self.appointment.id))
        self.assertEqual(response.data["amount"], "50.00")
        self.assertEqual(response.data["status"], Payment.Status.PENDING)
        self.assertEqual(response.data["payment_method"], Payment.Method.PIX)
        self.assertTrue(response.data["payment_code"])

    def test_repeated_create_returns_existing_payment(self):
        self.client.force_authenticate(user=self.customer)
        payload = {"appointment_id": str(self.appointment.id)}

        first_response = self.client.post(
            self.create_url(),
            payload,
            HTTP_IDEMPOTENCY_KEY="api-repeat-key",
            format="json",
        )
        second_response = self.client.post(
            self.create_url(),
            payload,
            HTTP_IDEMPOTENCY_KEY="api-repeat-key",
            format="json",
        )

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_response.data["id"], first_response.data["id"])

    def test_user_retrieves_own_payment(self):
        payment, _ = create_payment_for_appointment(
            self.customer,
            self.appointment.id,
            "api-detail-key",
        )
        self.client.force_authenticate(user=self.customer)

        response = self.client.get(self.detail_url(payment))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(payment.id))

    def test_user_cannot_retrieve_other_customer_payment(self):
        payment, _ = create_payment_for_appointment(
            self.customer,
            self.appointment.id,
            "api-other-detail-key",
        )
        self.client.force_authenticate(user=self.other_customer)

        response = self.client.get(self.detail_url(payment))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_public_webhook_confirms_payment(self):
        payment, _ = create_payment_for_appointment(
            self.customer,
            self.appointment.id,
            "api-webhook-key",
        )

        response = self.client.post(
            reverse("payment-webhook"),
            {
                "id": "api-event-1",
                "provider_payment_id": payment.provider_payment_id,
                "status": "paid",
                "type": "payment",
                "action": "payment.updated",
            },
            format="json",
        )

        payment.refresh_from_db()
        self.appointment.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(payment.status, Payment.Status.PAID)
        self.assertEqual(self.appointment.status, Appointment.Status.CONFIRMED)


class FakeHTTPResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class MercadoPagoGatewayTests(TestCase):
    @override_settings(
        MERCADO_PAGO_ACCESS_TOKEN="APP_USR-test",
        MERCADO_PAGO_WEBHOOK_SECRET="secret",
    )
    def test_creates_pix_charge_mapping_provider_response(self):
        response_payload = {
            "id": 123456,
            "status": "pending",
            "date_of_expiration": "2026-07-26T12:00:00-04:00",
            "point_of_interaction": {
                "transaction_data": {
                    "ticket_url": "https://mercadopago.test/ticket",
                    "qr_code": "pix-code",
                    "qr_code_base64": "base64-code",
                }
            },
        }
        gateway = MercadoPagoPaymentGateway()

        with self.patch_urlopen(response_payload) as urlopen_mock:
            result = gateway.create_pix_charge(
                PixChargeRequest(
                    payment_id="payment-id",
                    idempotency_key="idempotency-key",
                    amount=Decimal("50.00"),
                    description="Servico",
                    payer_email="cliente@example.com",
                    notification_url="https://api.test/api/v1/payments/webhook/",
                )
            )

        request = urlopen_mock.call_args.args[0]
        self.assertEqual(result.provider, Payment.Provider.MERCADO_PAGO)
        self.assertEqual(result.provider_payment_id, "123456")
        self.assertEqual(result.checkout_url, "https://mercadopago.test/ticket")
        self.assertEqual(result.payment_code, "pix-code")
        self.assertEqual(result.qr_code_base64, "base64-code")
        self.assertEqual(request.headers["X-idempotency-key"], "idempotency-key")

    @override_settings(
        MERCADO_PAGO_ACCESS_TOKEN="APP_USR-test",
        MERCADO_PAGO_WEBHOOK_SECRET="secret",
    )
    def test_validates_webhook_signature_and_fetches_provider_payment(self):
        gateway = MercadoPagoPaymentGateway()
        data_id = "123456"
        request_id = "request-id"
        timestamp = "1704908010"
        manifest = f"id:{data_id};request-id:{request_id};ts:{timestamp};"
        signature = hmac.new(
            b"secret",
            msg=manifest.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()
        headers = {
            "x-signature": f"ts={timestamp},v1={signature}",
            "x-request-id": request_id,
        }
        response_payload = {
            "id": 123456,
            "status": "approved",
            "date_approved": "2026-07-26T12:00:00-04:00",
        }

        with self.patch_urlopen(response_payload):
            result = gateway.parse_webhook(
                {
                    "id": "event-id",
                    "type": "payment",
                    "action": "payment.updated",
                    "data": {"id": data_id},
                },
                headers,
                {},
            )

        self.assertTrue(result.paid)
        self.assertEqual(result.provider_payment_id, data_id)
        self.assertEqual(result.provider_status, "approved")

    @override_settings(
        MERCADO_PAGO_ACCESS_TOKEN="APP_USR-test",
        MERCADO_PAGO_WEBHOOK_SECRET="secret",
    )
    def test_rejects_invalid_webhook_signature(self):
        gateway = MercadoPagoPaymentGateway()

        with self.assertRaises(ValidationError):
            gateway.parse_webhook(
                {
                    "id": "event-id",
                    "type": "payment",
                    "action": "payment.updated",
                    "data": {"id": "123456"},
                },
                {
                    "x-signature": "ts=1704908010,v1=invalid",
                    "x-request-id": "request-id",
                },
                {},
            )

    def patch_urlopen(self, payload):
        from unittest.mock import patch

        return patch(
            "payments.gateways.mercado_pago.urlopen",
            return_value=FakeHTTPResponse(payload),
        )
