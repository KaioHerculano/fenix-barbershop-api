from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema

from payments.serializers import PaymentCreateSerializer, PaymentSerializer

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
        "Nesta etapa o pagamento ainda nao chama o gateway Pix real."
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
