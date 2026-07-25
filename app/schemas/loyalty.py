from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema

from loyalty.serializers import (
    LoyaltyRedeemSerializer,
    LoyaltySummarySerializer,
    LoyaltyTransactionSerializer,
)

company_slug_query_parameter = OpenApiParameter(
    name="company_slug",
    description="Filtra o saldo ou historico por barbearia.",
    required=False,
    type=str,
    location=OpenApiParameter.QUERY,
)

loyalty_me_schema = extend_schema(
    summary="Consultar meu cartao fidelidade",
    description="Retorna saldo total e cartoes fidelidade do usuario autenticado.",
    parameters=[company_slug_query_parameter],
    responses={200: LoyaltySummarySerializer},
)

loyalty_transactions_schema = extend_schema(
    summary="Listar meu historico de pontos",
    description="Lista ganhos, resgates e ajustes do usuario autenticado.",
    parameters=[company_slug_query_parameter],
    responses={200: LoyaltyTransactionSerializer(many=True)},
)

loyalty_redeem_schema = extend_schema(
    summary="Resgatar pontos",
    description="Registra um resgate de pontos quando o usuario possui saldo suficiente.",
    request=LoyaltyRedeemSerializer,
    responses={201: LoyaltyTransactionSerializer, 400: None, 404: None},
    examples=[
        OpenApiExample(
            "Resgate",
            value={
                "company_slug": "fenix-barbershop",
                "points": 3,
                "description": "Resgate de beneficio no balcao",
            },
            request_only=True,
        )
    ],
)
