import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    class Provider(models.TextChoices):
        INTERNAL = "internal", "Internal"
        MERCADO_PAGO = "mercado_pago", "Mercado Pago"

    ACTIVE_STATUSES = [Status.PENDING]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="payments",
    )
    appointment = models.ForeignKey(
        "scheduling.Appointment",
        on_delete=models.PROTECT,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    provider = models.CharField(
        max_length=30,
        choices=Provider.choices,
        default=Provider.INTERNAL,
    )
    provider_payment_id = models.CharField(max_length=120, blank=True)
    idempotency_key = models.CharField(max_length=120, unique=True)
    pix_qr_code = models.TextField(blank=True)
    pix_copy_paste = models.TextField(blank=True)
    raw_response = models.JSONField(default=dict, blank=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"], name="payment_user_status_idx"),
            models.Index(
                fields=["appointment", "status"],
                name="payment_appointment_status_idx",
            ),
            models.Index(fields=["provider_payment_id"], name="payment_provider_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="payment_amount_positive",
            ),
            models.UniqueConstraint(
                fields=["appointment"],
                condition=Q(status="pending"),
                name="unique_pending_payment_per_appointment",
            ),
        ]

    def clean(self):
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({"amount": "Valor do pagamento deve ser positivo."})
        if self.appointment_id and self.user_id:
            if self.appointment.customer_id != self.user_id:
                raise ValidationError(
                    {
                        "appointment": "Pagamento deve pertencer ao cliente do agendamento."
                    }
                )
            if self.appointment.company_id != self.appointment.service.company_id:
                raise ValidationError(
                    {"appointment": "Agendamento deve pertencer a empresa do servico."}
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.appointment_id} - {self.status}"
