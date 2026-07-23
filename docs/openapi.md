# Referencia OpenAPI

A referencia OpenAPI continua sendo gerada pela aplicacao Django com drf-spectacular.

## Swagger UI

```text
http://localhost:8000/api/docs/
```

## Redoc

```text
http://localhost:8000/api/redoc/
```

## Schema JSON

```text
http://localhost:8000/api/schema/
```

## Quando atualizar

Sempre que uma rota, payload ou resposta mudar, atualize:

- serializers;
- schemas em `app/schemas/`;
- testes;
- esta documentacao em `docs/`.

O MkDocs explica os fluxos e decisoes de produto. O Redoc/Swagger devem continuar sendo a referencia tecnica detalhada dos contratos HTTP.
