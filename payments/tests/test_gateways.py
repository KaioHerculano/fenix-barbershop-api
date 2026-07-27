import hashlib
import hmac
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework.exceptions import ValidationError

from payments.gateways.base import PixChargeRequest
from payments.gateways.mercado_pago import MercadoPagoPaymentGateway
from payments.models import Payment
from payments.tests.factories import FakeHTTPResponse


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
        return patch(
            "payments.gateways.mercado_pago.urlopen",
            return_value=FakeHTTPResponse(payload),
        )
