import uuid

from django.core.exceptions import ValidationError
from django.db import models

from accounts.models import User


class BarberService(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    barber = models.ForeignKey(
        "company.CompanyEmployee",
        on_delete=models.CASCADE,
        related_name="barber_services",
    )
    service = models.ForeignKey(
        "services.Service",
        on_delete=models.CASCADE,
        related_name="barber_services",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["barber", "service"],
                name="unique_barber_service",
            ),
        ]
        ordering = ["barber__user__full_name", "service__name"]

    def clean(self):
        if self.barber_id and self.barber.role != User.Role.BARBER:
            raise ValidationError(
                {"barber": "Funcionário deve ter perfil de barbeiro."}
            )
        if (
            self.barber_id
            and self.service_id
            and self.barber.company_id != self.service.company_id
        ):
            raise ValidationError(
                {"service": "Serviço e barbeiro devem pertencer à mesma empresa."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.barber.user.full_name} - {self.service.name}"
