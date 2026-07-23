from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from accounts.models import CustomerProfile, User
from notifications.tasks import send_password_reset_email, send_welcome_email


class CustomerRegistrationService:
    @staticmethod
    def register_customer(email, full_name, phone, password):
        with transaction.atomic():
            user = User.objects.create_user(
                email=email,
                full_name=full_name,
                password=password,
                phone=phone,
            )
            CustomerProfile.objects.create(user=user)
            transaction.on_commit(lambda: send_welcome_email.delay(str(user.id)))
            return user


class PasswordResetService:
    @staticmethod
    def request_reset(email):
        user = User.objects.filter(email=email).first()
        if user:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            send_password_reset_email.delay(str(user.id), uid, token)

        return None

    @staticmethod
    def confirm_reset(uidb64, token, new_password):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.set_password(new_password)
            user.save()
            return True
        return False
