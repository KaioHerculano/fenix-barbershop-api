# Docker e operacao local

## Servicos do Compose

| Servico | Funcao |
| --- | --- |
| `db` | PostgreSQL |
| `redis` | Broker Celery |
| `web` | API Django |
| `celery` | Worker de tasks |
| `docs` | Documentacao MkDocs servida por Nginx |

## Subir tudo

```bash
docker compose up --build
```

## Acessar documentacao

```text
http://localhost:8001
```

## Atualizar documentacao

Edite arquivos em `docs/` e `mkdocs.yml`.

Para testar localmente com MkDocs fora do Docker:

```bash
pip install -r requirements_docs.txt
mkdocs serve
```

## OpenAPI e Redoc

A documentacao interativa da API continua sendo gerada pela propria aplicacao:

```text
http://localhost:8000/api/docs/
http://localhost:8000/api/redoc/
http://localhost:8000/api/schema/
```
