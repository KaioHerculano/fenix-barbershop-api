# Fenix BarberShop API

Backend da Fenix BarberShop, uma API em Django REST Framework para gestao de barbearias, catalogo publico, barbeiros, agenda, convites e notificacoes transacionais.

O projeto esta em desenvolvimento. A documentacao descreve o estado atual da API, sem incluir funcionalidades planejadas como se ja estivessem prontas.

## Stack

- Python 3.13
- Django 6
- Django REST Framework
- PostgreSQL
- Redis
- Celery
- drf-spectacular
- MkDocs Material
- Docker Compose

## Subir ambiente local

```bash
docker compose up --build
```

Servicos principais:

| Servico | URL |
| --- | --- |
| API | `http://localhost:8000` |
| Swagger UI | `http://localhost:8000/api/docs/` |
| Redoc | `http://localhost:8000/api/redoc/` |
| OpenAPI JSON | `http://localhost:8000/api/schema/` |
| MkDocs | `http://localhost:8001` |

## Documentacao

A documentacao principal fica em `docs/` e e servida por MkDocs.

Para rodar localmente fora do Docker:

```bash
pip install -r requirements_docs.txt
mkdocs serve
```

Para gerar build estatico:

```bash
mkdocs build --strict
```

## Testes e qualidade

```bash
make lint
make test-coverage
```

## Modulos

| Modulo | Responsabilidade |
| --- | --- |
| `accounts` | Usuarios, cadastro, login JWT, perfil e reset de senha |
| `company` | Empresas, funcionarios e convites de barbeiro |
| `services` | Catalogo publico de servicos |
| `barbers` | Barbeiros publicos e servicos executados |
| `scheduling` | Horarios, disponibilidade e agendamentos |
| `notifications` | Conteudo, envio e tasks de e-mail |
| `payments` | Reservado para pagamentos futuros |
| `loyalty` | Reservado para fidelidade futura |

## Fluxos ja suportados

- Cadastro de owner com criacao de empresa.
- Cadastro de cliente.
- Login JWT e refresh.
- Perfil autenticado.
- Catalogo publico de servicos.
- Listagem publica de barbeiros.
- Horarios publicos de funcionamento.
- Disponibilidade de agenda.
- Criacao, listagem, detalhe, cancelamento e reagendamento de agendamentos.
- Convite para usuario se tornar barbeiro.
- E-mails transacionais via Celery.

## Variaveis de ambiente

Use `.env.example` como referencia para criar `.env`.

Principais variaveis:

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `FRONTEND_URL`
- `RESEND_API_KEY`
- `RESEND_FROM_EMAIL`
