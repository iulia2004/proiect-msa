from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="pet",
            name="location",
            field=models.CharField(
                choices=[
                    ("interior", "Interior"),
                    ("exterior", "Exterior"),
                    ("ambele", "Interior și exterior"),
                ],
                default="interior",
                max_length=10,
                verbose_name="Unde stă animalul",
            ),
        ),
    ]
