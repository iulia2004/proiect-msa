from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_scan_pet"),
    ]

    operations = [
        migrations.AlterField(
            model_name="plant",
            name="photo",
            field=models.ImageField(blank=True, upload_to="plants/", verbose_name="Poză"),
        ),
    ]
