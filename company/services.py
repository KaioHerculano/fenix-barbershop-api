from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import (
    NotAuthenticated,
    PermissionDenied,
    ValidationError,
)

from accounts.models import User
from barbers.models import BarberService
from company.models import CompanyEmployee, StaffInvitation
from services.models import Service


def user_is_company_owner(user, company):
    return CompanyEmployee.objects.filter(
        user=user,
        company=company,
        role=User.Role.OWNER,
        is_active=True,
    ).exists()


def create_staff_invitation(company, invited_by, validated_data):
    token, token_digest = StaffInvitation.build_token()
    service_ids = validated_data.pop("service_ids", [])
    with transaction.atomic():
        if StaffInvitation.objects.filter(
            company=company,
            email=validated_data["email"].lower(),
            accepted_at__isnull=True,
            expires_at__gt=timezone.now(),
        ).exists():
            raise ValidationError(
                {"email": "Ja existe convite pendente para este e-mail."}
            )

        invitation = StaffInvitation.objects.create(
            company=company,
            email=validated_data["email"].lower(),
            full_name=validated_data.get("full_name", ""),
            role=User.Role.BARBER,
            invited_by=invited_by,
            token_digest=token_digest,
            expires_at=StaffInvitation.default_expiration(),
        )
        if service_ids:
            services = Service.objects.filter(
                id__in=service_ids,
                company=company,
                is_active=True,
            )
            invitation.services.set(services)

        from notifications.tasks import send_staff_invitation_email

        transaction.on_commit(
            lambda: send_staff_invitation_email.delay(str(invitation.id), token)
        )
        invitation.raw_token = token
        return invitation


def get_invitation_by_token(token):
    return get_object_or_404(
        StaffInvitation.objects.select_related(
            "company",
            "invited_by",
            "accepted_by",
        ).prefetch_related("services"),
        token_digest=StaffInvitation.digest_token(token),
    )


def validate_invitation_can_be_accepted(invitation):
    if invitation.is_accepted:
        raise ValidationError({"token": "Convite ja foi aceito."})
    if invitation.is_expired:
        raise ValidationError({"token": "Convite expirado."})


def validate_new_user_password(password, user=None):
    try:
        validate_password(password, user=user)
    except DjangoValidationError as exc:
        raise ValidationError({"password": list(exc.messages)})


def resolve_invited_user(invitation, request_user, validated_data):
    existing_user = User.objects.filter(email__iexact=invitation.email).first()
    if request_user.is_authenticated:
        if request_user.email.lower() != invitation.email.lower():
            raise PermissionDenied("Convite pertence a outro e-mail.")
        return request_user

    if existing_user:
        raise NotAuthenticated("Faca login para aceitar este convite.")

    password = validated_data.get("password")
    password_confirmation = validated_data.get("password_confirmation")
    full_name = validated_data.get("full_name") or invitation.full_name
    if not full_name:
        raise ValidationError({"full_name": "Nome completo e obrigatorio."})
    if not password:
        raise ValidationError({"password": "Senha e obrigatoria."})
    if password != password_confirmation:
        raise ValidationError({"password_confirmation": "As senhas nao coincidem."})

    user = User(email=invitation.email, full_name=full_name)
    validate_new_user_password(password, user=user)
    user = User.objects.create_user(
        email=invitation.email,
        full_name=full_name,
        password=password,
    )
    from notifications.tasks import send_welcome_email

    transaction.on_commit(lambda: send_welcome_email.delay(str(user.id)))
    return user


def accept_staff_invitation(token, request_user, validated_data):
    with transaction.atomic():
        invitation = get_object_or_404(
            StaffInvitation.objects.select_for_update().select_related(
                "company",
            ),
            token_digest=StaffInvitation.digest_token(token),
        )
        invitation.services.all()
        validate_invitation_can_be_accepted(invitation)
        user = resolve_invited_user(invitation, request_user, validated_data)
        employee, created = CompanyEmployee.objects.get_or_create(
            user=user,
            company=invitation.company,
            defaults={"role": User.Role.BARBER, "is_active": True},
        )
        if not created:
            employee.role = User.Role.BARBER
            employee.is_active = True
            employee.save(update_fields=["role", "is_active", "updated_at"])

        for service in invitation.services.filter(
            company=invitation.company,
            is_active=True,
        ):
            BarberService.objects.get_or_create(
                barber=employee,
                service=service,
                defaults={"is_active": True},
            )

        invitation.accepted_by = user
        invitation.accepted_at = timezone.now()
        invitation.save(update_fields=["accepted_by", "accepted_at", "updated_at"])
        return employee
