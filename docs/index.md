# Fenix BarberShop API

A Fenix BarberShop API e o backend do ecossistema de barbearias da Fenix. A aplicacao esta em desenvolvimento e esta documentacao descreve somente o que existe hoje no codigo.

## O que a API ja cobre

- Cadastro de owner com criacao de empresa.
- Cadastro de clientes.
- Login JWT e refresh de token.
- Perfil autenticado do usuario.
- Recuperacao de senha por e-mail transacional.
- Catalogo publico de servicos por barbearia.
- Listagem publica de barbeiros e servicos executados.
- Horarios publicos de funcionamento.
- Disponibilidade de agenda.
- Criacao, listagem, detalhe, cancelamento e reagendamento de agendamentos.
- Convite de barbeiro por link seguro.
- E-mails transacionais via tasks assicronas.

## O que ainda nao faz parte do escopo atual

- Painel administrativo via API para criar servicos e horarios.
- Pagamentos Pix.
- Reserva temporaria de horario.
- Bloqueios manuais de agenda.
- Notificacoes por WhatsApp/SMS.
- Fidelidade, no-show, fila de espera ou relatorios.

## Links rapidos

- Swagger UI: `/api/docs/`
- Redoc: `/api/redoc/`
- OpenAPI JSON: `/api/schema/`
- Documentacao MkDocs: porta `8001` no Docker Compose
