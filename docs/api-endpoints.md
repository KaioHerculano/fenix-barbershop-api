# API Endpoints

Base local:

```text
http://localhost:8000
```

## Accounts

| Metodo | Rota | Auth | Descricao |
| --- | --- | --- | --- |
| `POST` | `/api/v1/accounts/login/` | Nao | Gera tokens JWT |
| `POST` | `/api/v1/accounts/token/refresh/` | Nao | Renova access token |
| `POST` | `/api/v1/accounts/register/owner/` | Nao | Cria empresa e owner |
| `POST` | `/api/v1/accounts/register/customer/` | Nao | Cria cliente |
| `GET` | `/api/v1/accounts/me/` | Sim | Retorna perfil autenticado |
| `PATCH` | `/api/v1/accounts/me/` | Sim | Atualiza nome e telefone |
| `POST` | `/api/v1/accounts/password-reset/` | Nao | Solicita reset de senha |
| `POST` | `/api/v1/accounts/password-reset/confirm/` | Nao | Confirma nova senha |

## Catalogo publico

| Metodo | Rota | Auth | Descricao |
| --- | --- | --- | --- |
| `GET` | `/api/v1/companies/{company_slug}/services/` | Nao | Lista servicos ativos |
| `GET` | `/api/v1/companies/{company_slug}/services/{service_id}/` | Nao | Detalha servico ativo |
| `GET` | `/api/v1/companies/{company_slug}/barbers/` | Nao | Lista barbeiros ativos |
| `GET` | `/api/v1/companies/{company_slug}/barbers/{barber_id}/` | Nao | Detalha barbeiro ativo |
| `GET` | `/api/v1/companies/{company_slug}/barbers/{barber_id}/services/` | Nao | Lista servicos do barbeiro |
| `GET` | `/api/v1/companies/{company_slug}/working-hours/` | Nao | Lista horarios ativos |

## Convites de barbeiro

| Metodo | Rota | Auth | Descricao |
| --- | --- | --- | --- |
| `POST` | `/api/v1/companies/{company_slug}/staff-invitations/` | Owner | Cria convite de barbeiro |
| `GET` | `/api/v1/invitations/{token}/` | Nao | Consulta convite por token |
| `POST` | `/api/v1/invitations/{token}/accept/` | Condicional | Aceita convite |

## Agenda

| Metodo | Rota | Auth | Descricao |
| --- | --- | --- | --- |
| `GET` | `/api/v1/companies/{company_slug}/scheduling/availability/` | Nao | Lista slots disponiveis |
| `POST` | `/api/v1/companies/{company_slug}/appointments/` | Sim | Cria agendamento |
| `GET` | `/api/v1/companies/{company_slug}/appointments/` | Sim | Lista meus agendamentos |
| `GET` | `/api/v1/companies/{company_slug}/appointments/{appointment_id}/` | Sim | Detalha meu agendamento |
| `PATCH` | `/api/v1/companies/{company_slug}/appointments/{appointment_id}/cancel/` | Sim | Cancela meu agendamento |
| `PATCH` | `/api/v1/companies/{company_slug}/appointments/{appointment_id}/reschedule/` | Sim | Reagenda meu agendamento |
| `PATCH` | `/api/v1/companies/{company_slug}/appointments/{appointment_id}/complete/` | Owner ou barbeiro | Conclui agendamento e gera pontos |

## Fidelidade

| Metodo | Rota | Auth | Descricao |
| --- | --- | --- | --- |
| `GET` | `/api/v1/loyalty/me/` | Sim | Retorna saldo e cartoes fidelidade |
| `GET` | `/api/v1/loyalty/transactions/` | Sim | Lista historico de pontos |
| `POST` | `/api/v1/loyalty/redeem/` | Sim | Registra resgate de pontos |

## Pagamentos

| Metodo | Rota | Auth | Descricao |
| --- | --- | --- | --- |
| `POST` | `/api/v1/payments/create/` | Sim | Cria ou retorna pagamento Pix pendente de um agendamento |
| `GET` | `/api/v1/payments/{payment_id}/` | Sim | Consulta pagamento do usuario autenticado |
| `POST` | `/api/v1/payments/webhook/` | Nao | Recebe webhook do gateway de pagamento |

## Documentacao tecnica

| Metodo | Rota | Auth | Descricao |
| --- | --- | --- | --- |
| `GET` | `/api/schema/` | Nao | OpenAPI JSON |
| `GET` | `/api/docs/` | Nao | Swagger UI |
| `GET` | `/api/redoc/` | Nao | Redoc |
