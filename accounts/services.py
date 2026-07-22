import logging

from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from accounts.models import CustomerProfile, User

logger = logging.getLogger(__name__)


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
            return user


class PasswordResetService:
    @staticmethod
    def request_reset(email):
        user = User.objects.filter(email=email).first()
        if user:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            msg = (
                f"\n=== PASSWORD RESET REQUESTED ===\n"
                f"Usuario: {email}\n"
                f"Link simulado: http://localhost:8000/reset?uid={uid}&token={token}\n"
                f"UID: {uid}\n"
                f"TOKEN: {token}\n"
                f"================================"
            )
            logger.info(msg)
            print(msg)

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
