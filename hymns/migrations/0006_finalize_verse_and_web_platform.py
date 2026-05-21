import django.db.models.deletion
from django.db import migrations, models


def remove_orphan_verses(apps, schema_editor):
    Verse = apps.get_model("hymns", "Verse")
    Verse.objects.filter(denomination_hymn__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("hymns", "0005_category_denominations"),
    ]

    operations = [
        migrations.RunPython(remove_orphan_verses, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="subscription",
            name="platform",
            field=models.CharField(
                blank=True,
                choices=[
                    ("ios", "iOS"),
                    ("android", "Android"),
                    ("web", "Web"),
                ],
                max_length=20,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="verse",
            name="denomination_hymn",
            field=models.ForeignKey(
                help_text="Verses are linked to a specific denomination/period combination",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="verses",
                to="hymns.denominationhymn",
            ),
        ),
    ]
