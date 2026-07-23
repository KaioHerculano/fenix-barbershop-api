# Arquitetura

## Stack atual

- Django 6.
- Django REST Framework.
- drf-spectacular para OpenAPI, Swagger UI e Redoc.
- PostgreSQL.
- Redis.
- Celery.
- Resend para e-mails transacionais.
- MkDocs Material para documentacao estatica.

## Organizacao de camadas

| Camada | Exemplo | Responsabilidade |
| --- | --- | --- |
| Models | `Appointment`, `StaffInvitation` | Estado persistido e invariantes simples |
| Serializers | `AppointmentCreateSerializer` | Entrada e saida da API |
| Views | `AppointmentListCreateView` | Interface HTTP |
| Services | `create_appointment`, `accept_staff_invitation` | Regras transacionais |
| Selectors | `get_available_slots` | Consultas e leitura de dados derivados |
| Tasks | `send_staff_invitation_email` | Execucao assincrona |

## Multiempresa

O isolamento por empresa e feito por `company_slug` nas rotas publicas e autenticadas escopadas por empresa.

Exemplo:

```text
/api/v1/companies/{company_slug}/services/
```

As consultas devem sempre filtrar por empresa para evitar vazamento entre tenants.

## Agenda

Agendamentos ocupam horario quando estao em status `pending` ou `confirmed`. Na fase atual, novos agendamentos sao criados como `confirmed`.

O `end_time` e calculado pela duracao do servico, e a disponibilidade considera:

- servico ativo;
- barbeiro ativo;
- vinculo ativo entre barbeiro e servico;
- horario de funcionamento ativo;
- conflitos com agendamentos existentes.
