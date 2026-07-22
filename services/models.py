import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class Service(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        "company.Company",
        on_delete=models.CASCADE,
        related_name="services",
    )
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    duration_minutes = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["company", "name"],
                name="unique_service_name_per_company",
            ),
            models.CheckConstraint(
                condition=Q(price__gt=0),
                name="service_price_positive",
            ),
            models.CheckConstraint(
                condition=Q(duration_minutes__gt=0),
                name="service_duration_positive",
            ),
        ]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} - {self.company.name}"
