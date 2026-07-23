# Notificacoes

As notificacoes atuais sao e-mails transacionais enviados por tasks Celery.

## Provedor

O envio real usa Resend por meio da variavel `RESEND_API_KEY`.

Se `RESEND_API_KEY` nao estiver configurada, o envio e ignorado de forma segura e a aplicacao registra aviso no log.

## E-mails existentes

| Evento | Destinatario | Task |
| --- | --- | --- |
| Conta criada | Usuario | `send_welcome_email` |
| Reset de senha | Usuario | `send_password_reset_email` |
| Agendamento confirmado | Cliente | `send_appointment_confirmation_email` |
| Agendamento cancelado | Cliente | `send_appointment_cancelled_email` |
| Convite de barbeiro | E-mail convidado | `send_staff_invitation_email` |

## Templates

Templates HTML ficam em:

```text
notifications/templates/notifications/
```

## Links

Links de reset e convite usam `FRONTEND_URL`.

Exemplos:

```text
{FRONTEND_URL}/reset-password?uid={uid}&token={token}
{FRONTEND_URL}/invitations/{token}
```

## Desenvolvimento local

Para testar convite sem e-mail real, deixe `RESEND_API_KEY` vazio. A resposta da criacao de convite retorna `dev_invitation_url` quando `DEBUG=True`.
