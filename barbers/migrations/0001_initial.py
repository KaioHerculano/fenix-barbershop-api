import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("company", "0002_companyemployee_is_active"),
        ("services", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="BarberService",
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
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "barber",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="barber_services",
                        to="company.companyemployee",
                    ),
                ),
                (
                    "service",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="barber_services",
                        to="services.service",
                    ),
                ),
            ],
            options={
                "ordering": ["barber__user__full_name", "service__name"],
            },
        ),
        migrations.AddConstraint(
            model_name="barberservice",
            constraint=models.UniqueConstraint(
                fields=("barber", "service"), name="unique_barber_service"
            ),
        ),
    ]
