from payments.gateways.base import (
    PaymentGateway,
    PaymentWebhookResult,
    PixChargeRequest,
    PixChargeResult,
)
from payments.models import Payment


class InternalPaymentGateway(PaymentGateway):
    provider = Payment.Provider.INTERNAL

    def create_pix_charge(self, request: PixChargeRequest) -> PixChargeResult:
        return PixChargeResult(
            provider=self.provider,
            provider_payment_id=f"internal-{request.payment_id}",
            status="pending",
            payment_method=Payment.Method.PIX,
            checkout_url=f"https://payments.local/{request.payment_id}",
            payment_code=f"internal-pix-code-{request.payment_id}",
            qr_code_base64="",
            provider_payload={
                "id": f"internal-{request.payment_id}",
                "status": "pending",
            },
        )

    def parse_webhook(self, payload, headers, query_params) -> PaymentWebhookResult:
        provider_payment_id = str(payload.get("provider_payment_id", ""))
        provider_event_id = str(
            payload.get("id")
            or f"{payload.get('action', 'payment.updated')}:{provider_payment_id}"
        )
        provider_status = str(payload.get("status", "paid"))
        return PaymentWebhookResult(
            provider=self.provider,
            provider_event_id=provider_event_id,
            provider_payment_id=provider_payment_id,
            event_type=str(payload.get("type", "payment")),
            action=str(payload.get("action", "payment.updated")),
            provider_status=provider_status,
            paid=provider_status == "paid",
            raw_payload=dict(payload),
        )
