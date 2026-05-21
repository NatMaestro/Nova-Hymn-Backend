from django.db import migrations, models


def link_existing_categories_to_catholic(apps, schema_editor):
    Category = apps.get_model("hymns", "Category")
    Denomination = apps.get_model("hymns", "Denomination")

    catholic = (
        Denomination.objects.filter(slug="catholic").first()
        or Denomination.objects.filter(name__iexact="Catholic").first()
    )
    if not catholic:
        return

    for category in Category.objects.all():
        category.denominations.add(catholic)


def unlink_existing_categories_from_catholic(apps, schema_editor):
    Category = apps.get_model("hymns", "Category")
    Denomination = apps.get_model("hymns", "Denomination")

    catholic = (
        Denomination.objects.filter(slug="catholic").first()
        or Denomination.objects.filter(name__iexact="Catholic").first()
    )
    if not catholic:
        return

    for category in Category.objects.all():
        category.denominations.remove(catholic)


class Migration(migrations.Migration):

    dependencies = [
        ("hymns", "0004_paymentledger"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="denominations",
            field=models.ManyToManyField(
                blank=True,
                help_text="Denominations this category should appear under",
                related_name="categories",
                to="hymns.denomination",
            ),
        ),
        migrations.RunPython(
            link_existing_categories_to_catholic,
            unlink_existing_categories_from_catholic,
        ),
    ]
