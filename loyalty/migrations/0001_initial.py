import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("accounts", "0002_customerprofile"),
        ("company", "0003_staffinvitation"),
        ("scheduling", "0002_appointment"),
    ]

    operations = [
        migrations.CreateModel(
            name="LoyaltyCard",
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
                ("points_balance", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="loyalty_cards",
                        to="company.company",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="loyalty_cards",
                        to="accounts.user",
                    ),
                ),
            ],
            options={
                "ordering": ["company__name"],
            },
        ),
        migrations.CreateModel(
            name="LoyaltyTransaction",
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
                    "type",
                    models.CharField(
                        choices=[
                            ("earn", "Earn"),
                            ("redeem", "Redeem"),
                            ("adjustment", "Adjustment"),
                        ],
                        max_length=20,
                    ),
                ),
                ("points", models.IntegerField()),
                ("description", models.CharField(max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "appointment",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="loyalty_transactions",
                        to="scheduling.appointment",
                    ),
                ),
                (
                    "card",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="transactions",
                        to="loyalty.loyaltycard",
                    ),
                ),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="loyalty_transactions",
                        to="company.company",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="loyalty_transactions",
                        to="accounts.user",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="loyaltycard",
            index=models.Index(
                fields=["user", "company"], name="loyalty_card_user_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="loyaltycard",
            constraint=models.UniqueConstraint(
                fields=("company", "user"), name="unique_loyalty_card_company_user"
            ),
        ),
        migrations.AddIndex(
            model_name="loyaltytransaction",
            index=models.Index(
                fields=["user", "company", "-created_at"],
                name="loyalty_tx_user_company_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="loyaltytransaction",
            index=models.Index(
                fields=["appointment", "type"], name="loyalty_tx_appt_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="loyaltytransaction",
            constraint=models.CheckConstraint(
                condition=models.Q(("points", 0), _negated=True),
                name="loyalty_transaction_points_not_zero",
            ),
        ),
        migrations.AddConstraint(
            model_name="loyaltytransaction",
            constraint=models.UniqueConstraint(
                condition=models.Q(
                    ("appointment__isnull", False),
                    ("type", "earn"),
                ),
                fields=("appointment",),
                name="unique_loyalty_earn_per_appointment",
            ),
        ),
    ]
