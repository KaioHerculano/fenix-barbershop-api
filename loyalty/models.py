import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class LoyaltyCard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        "company.Company",
        on_delete=models.CASCADE,
        related_name="loyalty_cards",
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="loyalty_cards",
    )
    points_balance = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["company__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "user"],
                name="unique_loyalty_card_company_user",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "company"], name="loyalty_card_user_idx"),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.company.name}"


class LoyaltyTransaction(models.Model):
    class Type(models.TextChoices):
        EARN = "earn", "Earn"
        REDEEM = "redeem", "Redeem"
        ADJUSTMENT = "adjustment", "Adjustment"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    card = models.ForeignKey(
        "loyalty.LoyaltyCard",
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    company = models.ForeignKey(
        "company.Company",
        on_delete=models.PROTECT,
        related_name="loyalty_transactions",
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="loyalty_transactions",
    )
    appointment = models.ForeignKey(
        "scheduling.Appointment",
        on_delete=models.PROTECT,
        related_name="loyalty_transactions",
        blank=True,
        null=True,
    )
    type = models.CharField(max_length=20, choices=Type.choices)
    points = models.IntegerField()
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=~Q(points=0),
                name="loyalty_transaction_points_not_zero",
            ),
            models.UniqueConstraint(
                fields=["appointment"],
                condition=Q(type="earn", appointment__isnull=False),
                name="unique_loyalty_earn_per_appointment",
            ),
        ]
        indexes = [
            models.Index(
                fields=["user", "company", "-created_at"],
                name="loyalty_tx_user_company_idx",
            ),
            models.Index(fields=["appointment", "type"], name="loyalty_tx_appt_idx"),
        ]

    def clean(self):
        if self.type in [self.Type.EARN, self.Type.REDEEM] and self.points <= 0:
            raise ValidationError({"points": "Pontos devem ser maiores que zero."})
        if self.type == self.Type.ADJUSTMENT and self.points == 0:
            raise ValidationError(
                {"points": "Ajuste deve ter valor diferente de zero."}
            )
        if self.appointment and self.appointment.company_id != self.company_id:
            raise ValidationError(
                {"appointment": "Agendamento deve pertencer a mesma empresa."}
            )
        if self.appointment and self.appointment.customer_id != self.user_id:
            raise ValidationError(
                {"appointment": "Agendamento deve pertencer ao mesmo usuario."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} - {self.type} - {self.points}"
