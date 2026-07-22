from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("company", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="companyemployee",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
    ]
