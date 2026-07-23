import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class WorkingHour(models.Model):
    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Segunda-feira"
        TUESDAY = 1, "Terça-feira"
        WEDNESDAY = 2, "Quarta-feira"
        THURSDAY = 3, "Quinta-feira"
        FRIDAY = 4, "Sexta-feira"
        SATURDAY = 5, "Sábado"
        SUNDAY = 6, "Domingo"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        "company.Company",
        on_delete=models.CASCADE,
        related_name="working_hours",
    )
    weekday = models.PositiveSmallIntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(start_time__lt=models.F("end_time")),
                name="working_hour_start_before_end",
            ),
        ]
        ordering = ["weekday", "start_time"]

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError(
                {"end_time": "Horário final deve ser maior que o inicial."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.company.name} - {self.get_weekday_display()}"


class Appointment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"
        EXPIRED = "expired", "Expired"

    BLOCKING_STATUSES = [Status.PENDING, Status.CONFIRMED]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        "company.Company",
        on_delete=models.CASCADE,
        related_name="appointments",
    )
    customer = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="appointments",
    )
    barber = models.ForeignKey(
        "company.CompanyEmployee",
        on_delete=models.CASCADE,
        related_name="appointments",
    )
    service = models.ForeignKey(
        "services.Service",
        on_delete=models.PROTECT,
        related_name="appointments",
    )
    appointment_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CONFIRMED,
    )
    notes = models.TextField(blank=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-appointment_date", "-start_time"]
        indexes = [
            models.Index(
                fields=["company", "barber", "appointment_date", "status"],
                name="appointment_schedule_idx",
            ),
            models.Index(
                fields=["customer", "appointment_date", "status"],
                name="appointment_customer_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(start_time__lt=models.F("end_time")),
                name="appointment_start_before_end",
            ),
        ]

    def __str__(self):
        return f"{self.customer.full_name} - {self.service.name}"
