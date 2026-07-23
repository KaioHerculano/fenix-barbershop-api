import os

from django.template.loader import render_to_string


def frontend_url(path):
    base_url = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
    return f"{base_url}{path}"


def welcome_email(user):
    context = {"name": user.full_name}
    return {
        "to": user.email,
        "subject": "Bem-vindo ao Fenix BarberShop",
        "html": render_to_string("notifications/welcome.html", context),
        "text": f"Ola, {user.full_name}. Sua conta no Fenix BarberShop foi criada.",
    }


def password_reset_email(user, uid, token):
    reset_url = frontend_url(f"/reset-password?uid={uid}&token={token}")
    context = {"name": user.full_name, "reset_url": reset_url}
    return {
        "to": user.email,
        "subject": "Redefinicao de senha",
        "html": render_to_string("notifications/password_reset.html", context),
        "text": f"Acesse {reset_url} para redefinir sua senha.",
    }


def appointment_confirmation_email(appointment):
    context = {"appointment": appointment}
    return {
        "to": appointment.customer.email,
        "subject": "Agendamento confirmado",
        "html": render_to_string(
            "notifications/appointment_confirmation.html", context
        ),
        "text": (
            f"Seu agendamento de {appointment.service.name} foi confirmado "
            f"para {appointment.appointment_date} as {appointment.start_time}."
        ),
    }


def appointment_cancelled_email(appointment):
    context = {"appointment": appointment}
    return {
        "to": appointment.customer.email,
        "subject": "Agendamento cancelado",
        "html": render_to_string("notifications/appointment_cancelled.html", context),
        "text": (
            f"Seu agendamento de {appointment.service.name} em "
            f"{appointment.appointment_date} foi cancelado."
        ),
    }


def staff_invitation_email(invitation, token):
    invitation_url = frontend_url(f"/invitations/{token}")
    context = {"invitation": invitation, "invitation_url": invitation_url}
    return {
        "to": invitation.email,
        "subject": f"Convite para atuar na {invitation.company.name}",
        "html": render_to_string("notifications/staff_invitation.html", context),
        "text": f"Acesse {invitation_url} para aceitar o convite.",
    }
