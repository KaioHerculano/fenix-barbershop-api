import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("payments", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="payment",
            old_name="pix_copy_paste",
            new_name="payment_code",
        ),
        migrations.RenameField(
            model_name="payment",
            old_name="pix_qr_code",
            new_name="qr_code_base64",
        ),
        migrations.RenameField(
            model_name="payment",
            old_name="raw_response",
            new_name="provider_payload",
        ),
        migrations.AddField(
            model_name="payment",
            name="checkout_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="payment",
            name="expires_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="payment",
            name="payment_method",
            field=models.CharField(
                choices=[("pix", "Pix")],
                default="pix",
                max_length=30,
            ),
        ),
        migrations.CreateModel(
            name="PaymentWebhookEvent",
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
                (
                    "provider",
                    models.CharField(
                        choices=[
                            ("internal", "Internal"),
                            ("mercado_pago", "Mercado Pago"),
                        ],
                        max_length=30,
                    ),
                ),
                ("provider_event_id", models.CharField(max_length=120)),
                ("provider_payment_id", models.CharField(blank=True, max_length=120)),
                ("event_type", models.CharField(blank=True, max_length=80)),
                ("action", models.CharField(blank=True, max_length=80)),
                ("raw_payload", models.JSONField(blank=True, default=dict)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(
                        fields=["provider", "provider_payment_id"],
                        name="payment_webhook_provider_idx",
                    ),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("provider", "provider_event_id"),
                        name="unique_payment_webhook_provider_event",
                    ),
                ],
            },
        ),
    ]
