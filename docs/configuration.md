# Configuracao

As configuracoes locais ficam em `.env`. Use `.env.example` como base.

## Variaveis principais

| Variavel | Obrigatoria | Descricao |
| --- | --- | --- |
| `SECRET_KEY` | Sim | Chave secreta do Django |
| `DEBUG` | Sim | Deve ser `False` em producao |
| `ALLOWED_HOSTS` | Sim | Hosts aceitos pela aplicacao |
| `POSTGRES_DB` | Sim | Nome do banco |
| `POSTGRES_USER` | Sim | Usuario do banco |
| `POSTGRES_PASSWORD` | Sim | Senha do banco |
| `POSTGRES_HOST` | Sim | Host do banco |
| `POSTGRES_PORT` | Sim | Porta do banco |
| `FRONTEND_URL` | Nao | Base usada nos links de reset e convite |
| `RESEND_API_KEY` | Nao | Chave da API Resend para envio real de e-mails |
| `RESEND_FROM_EMAIL` | Nao | Remetente usado nos e-mails transacionais |
| `PAYMENT_GATEWAY` | Nao | Gateway de pagamento ativo. Padrao: `internal` |
| `PAYMENT_WEBHOOK_BASE_URL` | Nao | Base publica usada para montar URL de webhook enviada ao gateway |
| `MERCADO_PAGO_ACCESS_TOKEN` | Nao | Access token usado pelo adapter Mercado Pago |
| `MERCADO_PAGO_WEBHOOK_SECRET` | Nao | Secret usado para validar assinatura dos webhooks Mercado Pago |

## Modo desenvolvimento para convites

Quando `DEBUG=True` e `RESEND_API_KEY` nao esta configurada, a rota de criacao de convite retorna `dev_invitation_url`.

Esse comportamento existe para testes locais. Em producao, ou quando `RESEND_API_KEY` esta preenchida, o link de convite nao e exposto na resposta.

## E-mails

O envio real usa Resend. Sem `RESEND_API_KEY`, o envio e ignorado de forma segura e fica registrado no log da aplicacao.

## Pagamentos

O gateway padrao e `internal`, usado para desenvolvimento e testes sem chamada externa.

Para criar cobrancas Pix reais via Mercado Pago, configure `PAYMENT_GATEWAY=mercado_pago`, `MERCADO_PAGO_ACCESS_TOKEN` e `PAYMENT_WEBHOOK_BASE_URL`.

Em producao, configure tambem `MERCADO_PAGO_WEBHOOK_SECRET` para validar a origem dos webhooks recebidos.

## LGPD

Rotas publicas devem expor somente dados minimos. Hoje, barbeiros publicos retornam `id`, `full_name` e servicos executados. Dados como telefone, permissoes internas e credenciais nao sao expostos no catalogo publico.
