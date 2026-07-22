import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("company", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="WorkingHour",
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
                    "weekday",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (0, "Segunda-feira"),
                            (1, "Terça-feira"),
                            (2, "Quarta-feira"),
                            (3, "Quinta-feira"),
                            (4, "Sexta-feira"),
                            (5, "Sábado"),
                            (6, "Domingo"),
                        ]
                    ),
                ),
                ("start_time", models.TimeField()),
                ("end_time", models.TimeField()),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="working_hours",
                        to="company.company",
                    ),
                ),
            ],
            options={
                "ordering": ["weekday", "start_time"],
            },
        ),
        migrations.AddConstraint(
            model_name="workinghour",
            constraint=models.CheckConstraint(
                condition=models.Q(("start_time__lt", models.F("end_time"))),
                name="working_hour_start_before_end",
            ),
        ),
    ]
