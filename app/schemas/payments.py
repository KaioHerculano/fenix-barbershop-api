from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema

from payments.serializers import (
    PaymentCreateSerializer,
    PaymentSerializer,
    PaymentWebhookSerializer,
)

idempotency_key_header = OpenApiParameter(
    name="Idempotency-Key",
    description="Chave opcional para repetir a mesma criacao sem duplicar pagamento.",
    required=False,
    type=str,
    location=OpenApiParameter.HEADER,
)

payment_id_parameter = OpenApiParameter(
    name="payment_id",
    description="Identificador do pagamento.",
    required=True,
    type=str,
    location=OpenApiParameter.PATH,
)

payment_create_schema = extend_schema(
    tags=["Pagamentos"],
    summary="Criar pagamento do agendamento",
    description=(
        "Cria ou retorna o pagamento pendente de um agendamento do usuario autenticado. "
        "Quando PAYMENT_GATEWAY=mercado_pago, cria a cobranca Pix no adapter Mercado Pago."
    ),
    parameters=[idempotency_key_header],
    request=PaymentCreateSerializer,
    responses={201: PaymentSerializer, 200: PaymentSerializer, 400: None, 404: None},
    examples=[
        OpenApiExample(
            "Pagamento",
            value={"appointment_id": "00000000-0000-0000-0000-000000000000"},
            request_only=True,
        )
    ],
)

payment_detail_schema = extend_schema(
    tags=["Pagamentos"],
    summary="Consultar pagamento",
    description="Retorna os dados de um pagamento do usuario autenticado.",
    parameters=[payment_id_parameter],
    responses={200: PaymentSerializer, 404: None},
)

payment_webhook_schema = extend_schema(
    tags=["Pagamentos"],
    summary="Receber webhook de pagamento",
    description=(
        "Recebe eventos do gateway configurado. Para Mercado Pago, valida assinatura "
        "quando MERCADO_PAGO_WEBHOOK_SECRET esta configurado, busca o pagamento no provider "
        "e processa o evento com idempotencia."
    ),
    request=PaymentWebhookSerializer,
    auth=[],
    responses={200: None, 400: None, 404: None},
)
