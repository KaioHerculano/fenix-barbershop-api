from drf_spectacular.utils import extend_schema

from accounts.serializers import (CustomerRegistrationSerializer,
                                  OwnerRegistrationSerializer,
                                  PasswordResetConfirmSerializer,
                                  PasswordResetRequestSerializer,
                                  UserMeSerializer, UserMeUpdateSerializer)

owner_registration_schema = extend_schema(
    summary="Cadastro de Dono e Empresa",
    description="Cria uma nova empresa (Tenant) e o usuário administrador principal (Owner).",
    request=OwnerRegistrationSerializer,
    responses={
        201: {"type": "object", "properties": {"message": {"type": "string"}}},
        400: {
            "type": "object",
            "description": "Erros de validação (ex: e-mail duplicado)",
        },
    },
)

customer_registration_schema = extend_schema(
    summary="Cadastro de Cliente",
    description="Cria a conta do cliente para acessar a barbearia e se vincular ao Perfil (CustomerProfile).",
    request=CustomerRegistrationSerializer,
    responses={
        201: {"type": "object", "properties": {"message": {"type": "string"}}},
        400: {
            "type": "object",
            "description": "Erros de validação (ex: e-mail duplicado, senhas não coincidem)",
        },
    },
)

user_me_schema = extend_schema(
    summary="Perfil do Usuário Autenticado",
    description="GET: Busca dados do usuário. PATCH: Atualiza dados básicos.",
    methods=["GET", "PATCH"],
    request=UserMeUpdateSerializer,
    responses={
        200: UserMeSerializer,
        400: {"type": "object", "description": "Erros de validação na atualização"},
    },
)

password_reset_request_schema = extend_schema(
    summary="Solicitar Recuperação de Senha",
    description="Gera o link de recuperação (Nesta fase, o token é impresso no console).",
    request=PasswordResetRequestSerializer,
    responses={
        200: {"type": "object", "properties": {"message": {"type": "string"}}},
        400: {"type": "object", "description": "E-mail inválido"},
    },
)

password_reset_confirm_schema = extend_schema(
    summary="Confirmar Nova Senha",
    description="Recebe o token, uid e define a nova senha de acesso.",
    request=PasswordResetConfirmSerializer,
    responses={
        200: {"type": "object", "properties": {"message": {"type": "string"}}},
        400: {
            "type": "object",
            "description": "Token inválido, expirado ou senhas não coincidem",
        },
    },
)
