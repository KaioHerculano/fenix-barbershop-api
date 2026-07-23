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

## Modo desenvolvimento para convites

Quando `DEBUG=True` e `RESEND_API_KEY` nao esta configurada, a rota de criacao de convite retorna `dev_invitation_url`.

Esse comportamento existe para testes locais. Em producao, ou quando `RESEND_API_KEY` esta preenchida, o link de convite nao e exposto na resposta.

## E-mails

O envio real usa Resend. Sem `RESEND_API_KEY`, o envio e ignorado de forma segura e fica registrado no log da aplicacao.

## LGPD

Rotas publicas devem expor somente dados minimos. Hoje, barbeiros publicos retornam `id`, `full_name` e servicos executados. Dados como telefone, permissoes internas e credenciais nao sao expostos no catalogo publico.
