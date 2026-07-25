import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("scheduling", "0002_appointment"),
    ]

    operations = [
        migrations.CreateModel(
            name="Payment",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("paid", "Paid"),
                            ("failed", "Failed"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                (
                    "provider",
                    models.CharField(
                        choices=[
                            ("internal", "Internal"),
                            ("mercado_pago", "Mercado Pago"),
                        ],
                        default="internal",
                        max_length=30,
                    ),
                ),
                ("provider_payment_id", models.CharField(blank=True, max_length=120)),
                ("idempotency_key", models.CharField(max_length=120, unique=True)),
                ("pix_qr_code", models.TextField(blank=True)),
                ("pix_copy_paste", models.TextField(blank=True)),
                ("raw_response", models.JSONField(blank=True, default=dict)),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "appointment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="payments",
                        to="scheduling.appointment",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(
                        fields=["user", "status"],
                        name="payment_user_status_idx",
                    ),
                    models.Index(
                        fields=["appointment", "status"],
                        name="payment_appointment_status_idx",
                    ),
                    models.Index(
                        fields=["provider_payment_id"],
                        name="payment_provider_idx",
                    ),
                ],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("amount__gt", 0)),
                        name="payment_amount_positive",
                    ),
                    models.UniqueConstraint(
                        condition=models.Q(("status", "pending")),
                        fields=("appointment",),
                        name="unique_pending_payment_per_appointment",
                    ),
                ],
            },
        ),
    ]
