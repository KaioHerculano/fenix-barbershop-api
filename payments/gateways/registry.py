from django.conf import settings
from rest_framework.exceptions import ValidationError

from payments.gateways.internal import InternalPaymentGateway
from payments.gateways.mercado_pago import MercadoPagoPaymentGateway
from payments.models import Payment


def get_payment_gateway(provider=None):
    gateway_provider = provider or settings.PAYMENT_GATEWAY
    gateways = {
        Payment.Provider.INTERNAL: InternalPaymentGateway,
        Payment.Provider.MERCADO_PAGO: MercadoPagoPaymentGateway,
    }
    gateway_class = gateways.get(gateway_provider)
    if not gateway_class:
        raise ValidationError({"provider": "Gateway de pagamento nao suportado."})
    return gateway_class()
