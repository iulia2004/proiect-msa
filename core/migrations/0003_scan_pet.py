from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_pet_location"),
    ]

    operations = [
        migrations.AddField(
            model_name="scan",
            name="pet",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="scans",
                to="core.pet",
            ),
        ),
    ]
