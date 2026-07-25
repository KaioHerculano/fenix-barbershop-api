from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)

from accounts.serializers import (
    CustomerRegistrationSerializer,
    OwnerRegistrationSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserMeSerializer,
    UserMeUpdateSerializer,
)

token_obtain_pair_schema = extend_schema(
    tags=["Autenticação"],
    summary="Login",
    description="Autentica o usuario por e-mail e senha, retornando tokens JWT.",
    request=TokenObtainPairSerializer,
    responses={
        200: {
            "type": "object",
            "properties": {
                "refresh": {"type": "string"},
                "access": {"type": "string"},
            },
        },
        401: {"type": "object", "description": "Credenciais invalidas."},
    },
    examples=[
        OpenApiExample(
            "Login",
            value={"email": "owner@example.com", "password": "StrongPass123!"},
            request_only=True,
        )
    ],
)

token_refresh_schema = extend_schema(
    tags=["Autenticação"],
    summary="Renovar access token",
    description="Recebe um refresh token valido e retorna um novo access token.",
    request=TokenRefreshSerializer,
    responses={
        200: {
            "type": "object",
            "properties": {"access": {"type": "string"}},
        },
        401: {"type": "object", "description": "Refresh token invalido ou expirado."},
    },
    examples=[
        OpenApiExample(
            "Refresh",
            value={"refresh": "jwt-refresh-token"},
            request_only=True,
        )
    ],
)

owner_registration_schema = extend_schema(
    tags=["Cadastro"],
    summary="Cadastro de owner e empresa",
    description="Cria uma empresa e o usuario administrador principal com role OWNER.",
    request=OwnerRegistrationSerializer,
    responses={
        201: {"type": "object", "properties": {"message": {"type": "string"}}},
        400: {
            "type": "object",
            "description": "Erros de validacao, como e-mail ou slug duplicados.",
        },
    },
    examples=[
        OpenApiExample(
            "Owner",
            value={
                "company_name": "Fenix BarberShop",
                "company_slug": "fenix-barbershop",
                "full_name": "Owner Fenix",
                "email": "owner@example.com",
                "password": "StrongPass123!",
            },
            request_only=True,
        )
    ],
)

customer_registration_schema = extend_schema(
    tags=["Cadastro"],
    summary="Cadastro de cliente",
    description="Cria uma conta de cliente e o perfil usado para agendamentos.",
    request=CustomerRegistrationSerializer,
    responses={
        201: {"type": "object", "properties": {"message": {"type": "string"}}},
        400: {
            "type": "object",
            "description": "Erros de validacao, como e-mail duplicado ou senhas divergentes.",
        },
    },
    examples=[
        OpenApiExample(
            "Cliente",
            value={
                "full_name": "Cliente Fenix",
                "email": "cliente@example.com",
                "phone": "65999999999",
                "password": "StrongPass123!",
                "password_confirmation": "StrongPass123!",
            },
            request_only=True,
        )
    ],
)

user_me_schema = extend_schema(
    tags=["Cadastro"],
    summary="Perfil do usuario autenticado",
    description="Retorna ou atualiza dados basicos do usuario autenticado.",
    methods=["GET", "PATCH"],
    request=UserMeUpdateSerializer,
    responses={
        200: UserMeSerializer,
        400: {"type": "object", "description": "Erros de validacao na atualizacao."},
    },
)

password_reset_request_schema = extend_schema(
    tags=["Autenticação"],
    summary="Solicitar recuperacao de senha",
    description="Gera token de recuperacao e dispara e-mail transacional quando o e-mail existe.",
    request=PasswordResetRequestSerializer,
    responses={
        200: {"type": "object", "properties": {"message": {"type": "string"}}},
        400: {"type": "object", "description": "E-mail invalido."},
    },
    examples=[
        OpenApiExample(
            "Solicitacao",
            value={"email": "cliente@example.com"},
            request_only=True,
        )
    ],
)

password_reset_confirm_schema = extend_schema(
    tags=["Autenticação"],
    summary="Confirmar nova senha",
    description="Recebe uid, token e nova senha para concluir a recuperacao.",
    request=PasswordResetConfirmSerializer,
    responses={
        200: {"type": "object", "properties": {"message": {"type": "string"}}},
        400: {
            "type": "object",
            "description": "Token invalido, expirado ou senhas divergentes.",
        },
    },
    examples=[
        OpenApiExample(
            "Confirmacao",
            value={
                "uidb64": "MQ",
                "token": "token-gerado",
                "new_password": "NewStrong123!",
                "new_password_confirmation": "NewStrong123!",
            },
            request_only=True,
        )
    ],
)
