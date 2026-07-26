from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class PixChargeRequest:
    payment_id: str
    idempotency_key: str
    amount: Decimal
    description: str
    payer_email: str
    notification_url: str


@dataclass(frozen=True)
class PixChargeResult:
    provider: str
    provider_payment_id: str
    status: str
    payment_method: str
    checkout_url: str = ""
    payment_code: str = ""
    qr_code_base64: str = ""
    expires_at: datetime | None = None
    provider_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PaymentWebhookResult:
    provider: str
    provider_event_id: str
    provider_payment_id: str
    event_type: str
    action: str
    provider_status: str
    paid: bool
    raw_payload: dict[str, Any]
    paid_at: datetime | None = None


class PaymentGateway:
    provider: str

    def create_pix_charge(self, request: PixChargeRequest) -> PixChargeResult:
        raise NotImplementedError

    def parse_webhook(self, payload, headers, query_params) -> PaymentWebhookResult:
        raise NotImplementedError
