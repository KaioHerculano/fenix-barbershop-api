from celery import shared_task

from accounts.models import User
from company.models import StaffInvitation
from notifications import emails
from notifications.services import send_email
from scheduling.models import Appointment


@shared_task(bind=True, max_retries=3)
def send_welcome_email(self, user_id):
    user = User.objects.get(id=user_id)
    return send_email(emails.welcome_email(user))


@shared_task(bind=True, max_retries=3)
def send_password_reset_email(self, user_id, uid, token):
    user = User.objects.get(id=user_id)
    return send_email(emails.password_reset_email(user, uid, token))


@shared_task(bind=True, max_retries=3)
def send_appointment_confirmation_email(self, appointment_id):
    appointment = Appointment.objects.select_related(
        "customer", "barber__user", "service", "company"
    ).get(id=appointment_id)
    return send_email(emails.appointment_confirmation_email(appointment))


@shared_task(bind=True, max_retries=3)
def send_appointment_cancelled_email(self, appointment_id):
    appointment = Appointment.objects.select_related(
        "customer", "barber__user", "service", "company"
    ).get(id=appointment_id)
    return send_email(emails.appointment_cancelled_email(appointment))


@shared_task(bind=True, max_retries=3)
def send_staff_invitation_email(self, invitation_id, token):
    invitation = StaffInvitation.objects.select_related("company", "invited_by").get(
        id=invitation_id
    )
    return send_email(emails.staff_invitation_email(invitation, token))
