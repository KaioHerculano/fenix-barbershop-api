# Autenticacao e seguranca

## JWT

A API usa JWT via Simple JWT.

### Login

```http
POST /api/v1/accounts/login/
```

Payload:

```json
{
  "email": "owner@example.com",
  "password": "StrongPass123!"
}
```

Resposta:

```json
{
  "refresh": "jwt-refresh-token",
  "access": "jwt-access-token"
}
```

### Usar token

```http
Authorization: Bearer jwt-access-token
```

### Refresh

```http
POST /api/v1/accounts/token/refresh/
```

Payload:

```json
{
  "refresh": "jwt-refresh-token"
}
```

## Escopos de acesso atuais

| Recurso | Acesso |
| --- | --- |
| Cadastro de owner | Publico |
| Cadastro de cliente | Publico |
| Login e refresh | Publico |
| Catalogo publico | Publico |
| Disponibilidade | Publico |
| Meus agendamentos | Autenticado |
| Convite de barbeiro | Owner da empresa |
| Aceite de convite | Publico para novo usuario ou autenticado para usuario existente |

## Convites

O token de convite e exibido apenas no momento da criacao em ambiente local controlado. No banco fica salvo somente o hash do token.

## Reset de senha

O reset gera `uidb64` e `token`, e dispara e-mail transacional. A resposta da API nao revela se o e-mail existe, reduzindo risco de enumeracao de contas.
