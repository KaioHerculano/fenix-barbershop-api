import hashlib
import hmac
import json
from datetime import datetime
from decimal import Decimal
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from django.conf import settings
from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import ValidationError

from payments.gateways.base import (
    PaymentGateway,
    PaymentWebhookResult,
    PixChargeRequest,
    PixChargeResult,
)
from payments.models import Payment


class MercadoPagoPaymentGateway(PaymentGateway):
    provider = Payment.Provider.MERCADO_PAGO
    base_url = "https://api.mercadopago.com"

    def __init__(self, access_token=None, webhook_secret=None, timeout=20):
        self.access_token = access_token or settings.MERCADO_PAGO_ACCESS_TOKEN
        self.webhook_secret = webhook_secret or settings.MERCADO_PAGO_WEBHOOK_SECRET
        self.timeout = timeout

    def create_pix_charge(self, request: PixChargeRequest) -> PixChargeResult:
        if not self.access_token:
            raise ValidationError(
                {"provider": "MERCADO_PAGO_ACCESS_TOKEN nao configurado."}
            )

        payload = {
            "transaction_amount": float(self.normalize_amount(request.amount)),
            "description": request.description,
            "payment_method_id": "pix",
            "external_reference": request.payment_id,
            "notification_url": request.notification_url,
            "payer": {
                "email": request.payer_email,
            },
        }
        response = self.post(
            "/v1/payments",
            payload,
            idempotency_key=request.idempotency_key,
        )
        transaction_data = response.get("point_of_interaction", {}).get(
            "transaction_data", {}
        )
        return PixChargeResult(
            provider=self.provider,
            provider_payment_id=str(response.get("id", "")),
            status=str(response.get("status", "")),
            payment_method=Payment.Method.PIX,
            checkout_url=str(transaction_data.get("ticket_url", "")),
            payment_code=str(transaction_data.get("qr_code", "")),
            qr_code_base64=str(transaction_data.get("qr_code_base64", "")),
            expires_at=self.parse_provider_datetime(response.get("date_of_expiration")),
            provider_payload=response,
        )

    def parse_webhook(self, payload, headers, query_params) -> PaymentWebhookResult:
        data = payload.get("data", {}) if isinstance(payload, dict) else {}
        provider_payment_id = str(
            data.get("id")
            or query_params.get("data.id")
            or query_params.get("data_id")
            or ""
        )
        self.validate_signature(headers, provider_payment_id)
        provider_event_id = str(
            payload.get("id") or f"{payload.get('action')}:{provider_payment_id}"
        )
        provider_payment = self.get(f"/v1/payments/{provider_payment_id}")
        provider_status = str(provider_payment.get("status", ""))
        paid_at = self.parse_provider_datetime(
            provider_payment.get("date_approved")
            or provider_payment.get("money_release_date")
        )
        return PaymentWebhookResult(
            provider=self.provider,
            provider_event_id=provider_event_id,
            provider_payment_id=provider_payment_id,
            event_type=str(payload.get("type", "")),
            action=str(payload.get("action", "")),
            provider_status=provider_status,
            paid=provider_status == "approved",
            raw_payload={
                "webhook": dict(payload),
                "payment": provider_payment,
            },
            paid_at=paid_at,
        )

    def post(self, path, payload, idempotency_key):
        return self.request(
            "POST",
            path,
            payload=payload,
            extra_headers={"X-Idempotency-Key": idempotency_key},
        )

    def get(self, path):
        return self.request("GET", path)

    def request(self, method, path, payload=None, extra_headers=None):
        body = None
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if extra_headers:
            headers.update(extra_headers)
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")

        request = Request(
            f"{self.base_url}{path}",
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8")
            raise ValidationError({"provider": detail}) from exc

    def validate_signature(self, headers, provider_payment_id):
        if not self.webhook_secret:
            if settings.DEBUG:
                return
            raise ValidationError(
                {"signature": "MERCADO_PAGO_WEBHOOK_SECRET nao configurado."}
            )

        signature_header = headers.get("x-signature") or headers.get("X-Signature")
        request_id = headers.get("x-request-id") or headers.get("X-Request-Id")
        signature_parts = self.parse_signature_header(signature_header)
        timestamp = signature_parts.get("ts")
        received_hash = signature_parts.get("v1")
        if not timestamp or not received_hash:
            raise ValidationError({"signature": "Assinatura do webhook invalida."})

        manifest = (
            f"id:{provider_payment_id.lower()};request-id:{request_id};ts:{timestamp};"
        )
        expected_hash = hmac.new(
            self.webhook_secret.encode("utf-8"),
            msg=manifest.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected_hash, received_hash):
            raise ValidationError({"signature": "Assinatura do webhook invalida."})

    def parse_signature_header(self, signature_header):
        if not signature_header:
            return {}
        parts = {}
        for item in signature_header.split(","):
            key, _, value = item.partition("=")
            parts[key.strip()] = value.strip()
        return parts

    def normalize_amount(self, amount):
        return Decimal(amount).quantize(Decimal("0.01"))

    def parse_provider_datetime(self, value):
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        return parse_datetime(str(value))
