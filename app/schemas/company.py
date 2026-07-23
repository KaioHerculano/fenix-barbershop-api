from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema

from company.serializers import (
    StaffInvitationAcceptResponseSerializer,
    StaffInvitationAcceptSerializer,
    StaffInvitationCreateSerializer,
    StaffInvitationSerializer,
)

company_slug_parameter = OpenApiParameter(
    name="company_slug",
    description="Slug publico da barbearia.",
    required=True,
    type=str,
    location=OpenApiParameter.PATH,
)

token_parameter = OpenApiParameter(
    name="token",
    description="Token publico do convite.",
    required=True,
    type=str,
    location=OpenApiParameter.PATH,
)

staff_invitation_create_schema = extend_schema(
    summary="Convidar barbeiro",
    description="Cria um convite para barbeiro e dispara e-mail transacional.",
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
    description="Retorna dados publicos de um convite ainda identificado por token.",
    parameters=[token_parameter],
    responses={200: StaffInvitationSerializer, 404: None},
    auth=[],
)

staff_invitation_accept_schema = extend_schema(
    summary="Aceitar convite",
    description="Aceita um convite de barbeiro criando ou vinculando o usuario convidado.",
    parameters=[token_parameter],
    request=StaffInvitationAcceptSerializer,
    responses={200: StaffInvitationAcceptResponseSerializer, 400: None, 401: None},
)
