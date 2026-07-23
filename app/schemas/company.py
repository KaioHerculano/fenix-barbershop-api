from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema

from company.serializers import (
    StaffInvitationAcceptResponseSerializer,
    StaffInvitationAcceptSerializer,
    StaffInvitationCreateSerializer,
    StaffInvitationSerializer,
)

company_slug_parameter = OpenApiParameter(
    name="company_slug",
    description="Slug publico da empresa/barbearia.",
    required=True,
    type=str,
    location=OpenApiParameter.PATH,
)

token_parameter = OpenApiParameter(
    name="token",
    description="Token recebido no link de convite.",
    required=True,
    type=str,
    location=OpenApiParameter.PATH,
)

staff_invitation_create_schema = extend_schema(
    summary="Convidar barbeiro",
    description=(
        "Cria um convite para um usuario se tornar barbeiro da empresa. "
        "Apenas owners da empresa podem usar esta rota. Em desenvolvimento, "
        "quando DEBUG=True e RESEND_API_KEY esta vazio, a resposta inclui dev_invitation_url."
    ),
    parameters=[company_slug_parameter],
    request=StaffInvitationCreateSerializer,
    responses={201: StaffInvitationSerializer, 400: None, 403: None, 404: None},
    examples=[
        OpenApiExample(
            "Convite",
            value={
                "email": "barbeiro@example.com",
                "full_name": "Barbeiro Teste",
                "service_ids": ["00000000-0000-0000-0000-000000000000"],
            },
            request_only=True,
        )
    ],
)

staff_invitation_detail_schema = extend_schema(
    summary="Detalhar convite",
    description="Retorna dados publicos do convite identificado pelo token.",
    parameters=[token_parameter],
    responses={200: StaffInvitationSerializer, 404: None},
    auth=[],
)

staff_invitation_accept_schema = extend_schema(
    summary="Aceitar convite",
    description=(
        "Aceita um convite de barbeiro. Usuario existente deve estar autenticado "
        "com o mesmo e-mail do convite. Usuario novo pode informar nome e senha no payload."
    ),
    parameters=[token_parameter],
    request=StaffInvitationAcceptSerializer,
    responses={
        200: StaffInvitationAcceptResponseSerializer,
        400: None,
        401: None,
        403: None,
        404: None,
    },
    examples=[
        OpenApiExample(
            "Usuario novo",
            value={
                "full_name": "Barbeiro Teste",
                "password": "StrongPass123!",
                "password_confirmation": "StrongPass123!",
            },
            request_only=True,
        ),
        OpenApiExample("Usuario autenticado", value={}, request_only=True),
    ],
)
