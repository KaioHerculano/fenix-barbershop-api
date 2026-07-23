# Primeiros passos

## Requisitos

- Docker e Docker Compose.
- Python 3.13 para desenvolvimento local sem container.
- Poetry para instalar dependencias do backend fora do Docker.
- PostgreSQL e Redis quando rodar sem Compose.

## Subir a aplicacao com Docker Compose

```bash
docker compose up --build
```

Servicos principais:

| Servico | Porta | Uso |
| --- | --- | --- |
| API Django | `8000` | Backend e documentacao OpenAPI |
| PostgreSQL | `5432` | Banco de dados |
| Redis | `6379` | Broker do Celery |
| MkDocs | `8001` | Documentacao estatica |

## URLs locais

| Recurso | URL |
| --- | --- |
| API | `http://localhost:8000` |
| Swagger UI | `http://localhost:8000/api/docs/` |
| Redoc | `http://localhost:8000/api/redoc/` |
| OpenAPI JSON | `http://localhost:8000/api/schema/` |
| MkDocs | `http://localhost:8001` |

## Instalar dependencias sem Docker

```bash
poetry install
```

## Rodar migracoes

```bash
python manage.py migrate
```

## Rodar servidor local

```bash
python manage.py runserver
```
