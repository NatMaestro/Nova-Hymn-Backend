# Generated manually for seeding initial denominations

from django.db import migrations


def create_denominations(apps, schema_editor):
    """Create initial denominations: Catholic, Methodist, Baptist"""
    Denomination = apps.get_model('hymns', 'Denomination')
    
    denominations = [
        {'name': 'Catholic', 'slug': 'catholic', 'display_order': 1, 'description': 'Roman Catholic Church'},
        {'name': 'Methodist', 'slug': 'methodist', 'display_order': 2, 'description': 'Methodist Church'},
        {'name': 'Baptist', 'slug': 'baptist', 'display_order': 3, 'description': 'Baptist Church'},
    ]
    
    for denom_data in denominations:
        Denomination.objects.get_or_create(
            slug=denom_data['slug'],
            defaults=denom_data
        )


def reverse_denominations(apps, schema_editor):
    """Remove denominations"""
    Denomination = apps.get_model('hymns', 'Denomination')
    Denomination.objects.filter(slug__in=['catholic', 'methodist', 'baptist']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('hymns', '0002_add_denomination_system'),
    ]

    operations = [
        migrations.RunPython(create_denominations, reverse_denominations),
    ]



