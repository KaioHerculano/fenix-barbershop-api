# Fluxos principais

## Criar empresa e owner

```http
POST /api/v1/accounts/register/owner/
```

```json
{
  "company_name": "Fenix BarberShop",
  "company_slug": "fenix-barbershop",
  "full_name": "Owner Fenix",
  "email": "owner@example.com",
  "password": "StrongPass123!"
}
```

Resultado: cria `Company`, cria usuario owner e cria vinculo `CompanyEmployee` com role `OWNER`.

## Criar cliente

```http
POST /api/v1/accounts/register/customer/
```

```json
{
  "full_name": "Cliente Fenix",
  "email": "cliente@example.com",
  "phone": "65999999999",
  "password": "StrongPass123!",
  "password_confirmation": "StrongPass123!"
}
```

Resultado: cria usuario e `CustomerProfile`.

## Transformar usuario comum em barbeiro

1. O usuario comum se cadastra como cliente.
2. O owner faz login.
3. O owner cria convite.

```http
POST /api/v1/companies/{company_slug}/staff-invitations/
Authorization: Bearer owner-access-token
```

```json
{
  "email": "barbeiro@example.com",
  "full_name": "Barbeiro Fenix",
  "service_ids": ["00000000-0000-0000-0000-000000000000"]
}
```

Em desenvolvimento, sem `RESEND_API_KEY`, a resposta inclui:

```json
{
  "dev_invitation_url": "http://localhost:3000/invitations/token-do-convite"
}
```

4. O convidado consulta o convite, se quiser.

```http
GET /api/v1/invitations/{token}/
```

5. O convidado aceita o convite.

Usuario ja cadastrado deve estar autenticado com o mesmo e-mail do convite:

```http
POST /api/v1/invitations/{token}/accept/
Authorization: Bearer invited-user-access-token
```

```json
{}
```

Usuario ainda inexistente pode aceitar informando dados de criacao:

```json
{
  "full_name": "Barbeiro Fenix",
  "password": "StrongPass123!",
  "password_confirmation": "StrongPass123!"
}
```

Resultado: cria ou reutiliza usuario, cria vinculo `CompanyEmployee` com role `BARBER` e cria os vinculos de servicos.

## Consultar catalogo publico

```http
GET /api/v1/companies/{company_slug}/services/
GET /api/v1/companies/{company_slug}/barbers/
GET /api/v1/companies/{company_slug}/working-hours/
```

## Consultar disponibilidade

```http
GET /api/v1/companies/{company_slug}/scheduling/availability/?date=2026-07-25&barber_id={barber_id}&service_id={service_id}
```

Resultado:

```json
[
  {
    "start_time": "09:00",
    "end_time": "09:30"
  }
]
```

## Criar agendamento

```http
POST /api/v1/companies/{company_slug}/appointments/
Authorization: Bearer customer-access-token
```

```json
{
  "service_id": "00000000-0000-0000-0000-000000000000",
  "barber_id": "00000000-0000-0000-0000-000000000000",
  "appointment_date": "2026-07-25",
  "start_time": "09:00",
  "notes": "Preferencia por corte baixo"
}
```

Resultado: cria agendamento `pending`. O horario ja fica reservado porque agendamentos pendentes bloqueiam a agenda.

## Criar pagamento do agendamento

```http
POST /api/v1/payments/create/
Authorization: Bearer customer-access-token
Idempotency-Key: payment-create-key
```

```json
{
  "appointment_id": "00000000-0000-0000-0000-000000000000"
}
```

Resultado: cria ou retorna o pagamento pendente do agendamento autenticado, usando o valor do servico.

Quando `PAYMENT_GATEWAY=mercado_pago`, a resposta inclui dados de Pix retornados pelo gateway, como `payment_code`, `qr_code_base64` e `checkout_url`.

## Consultar pagamento

```http
GET /api/v1/payments/{payment_id}/
Authorization: Bearer customer-access-token
```

## Confirmar pagamento por webhook

```http
POST /api/v1/payments/webhook/
```

Resultado: processa o evento de forma idempotente. Quando o gateway informa pagamento aprovado, o pagamento vira `paid`, o agendamento vira `confirmed` e o e-mail de confirmacao e disparado.

## Cancelar agendamento

```http
PATCH /api/v1/companies/{company_slug}/appointments/{appointment_id}/cancel/
Authorization: Bearer customer-access-token
```

## Concluir agendamento e gerar pontos

```http
PATCH /api/v1/companies/{company_slug}/appointments/{appointment_id}/complete/
Authorization: Bearer owner-or-barber-access-token
```

Resultado: marca o agendamento como `completed` e gera 1 ponto para o cliente, caso esse agendamento ainda nao tenha pontuado.

Somente o owner da empresa ou o barbeiro responsavel pelo atendimento podem concluir o agendamento.

## Reagendar agendamento

```http
PATCH /api/v1/companies/{company_slug}/appointments/{appointment_id}/reschedule/
Authorization: Bearer customer-access-token
```

```json
{
  "appointment_date": "2026-07-26",
  "start_time": "10:30"
}
```

## Consultar fidelidade

```http
GET /api/v1/loyalty/me/
Authorization: Bearer customer-access-token
```

Com filtro por empresa:

```http
GET /api/v1/loyalty/me/?company_slug=fenix-barbershop
Authorization: Bearer customer-access-token
```

## Consultar historico de pontos

```http
GET /api/v1/loyalty/transactions/
Authorization: Bearer customer-access-token
```

## Resgatar pontos

```http
POST /api/v1/loyalty/redeem/
Authorization: Bearer customer-access-token
```

```json
{
  "company_slug": "fenix-barbershop",
  "points": 3,
  "description": "Resgate de beneficio no balcao"
}
```
