import uuid
from datetime import timedelta
from hashlib import sha256
from secrets import token_urlsafe

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from accounts.models import User


class Company(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=100)
    address = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"

    def __str__(self):
        return self.name


class CompanyEmployee(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
    )
    company = models.ForeignKey(
        "company.Company",
        on_delete=models.CASCADE,
    )
    role = models.CharField(max_length=20, choices=User.Role.choices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "company")

    def __str__(self):
        return f"{self.user.full_name} - {self.company.name}"


class StaffInvitation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        "company.Company",
        on_delete=models.CASCADE,
        related_name="staff_invitations",
    )
    email = models.EmailField()
    full_name = models.CharField(max_length=255, blank=True)
    role = models.CharField(
        max_length=20,
        choices=User.Role.choices,
        default=User.Role.BARBER,
    )
    services = models.ManyToManyField(
        "services.Service",
        blank=True,
        related_name="staff_invitations",
    )
    token_digest = models.CharField(max_length=64, unique=True)
    invited_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="sent_staff_invitations",
    )
    accepted_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        related_name="accepted_staff_invitations",
        blank=True,
        null=True,
    )
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["company", "email"], name="staff_invite_email_idx"),
            models.Index(fields=["token_digest"], name="staff_invite_token_idx"),
        ]

    @staticmethod
    def build_token():
        token = token_urlsafe(32)
        return token, StaffInvitation.digest_token(token)

    @staticmethod
    def digest_token(token):
        return sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def default_expiration():
        return timezone.now() + timedelta(days=7)

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @property
    def is_accepted(self):
        return self.accepted_at is not None

    def clean(self):
        if self.role != User.Role.BARBER:
            raise ValidationError({"role": "Convite deve ser para barbeiro."})

    def __str__(self):
        return f"{self.email} - {self.company.name}"
