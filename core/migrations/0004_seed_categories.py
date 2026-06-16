from django.db import migrations


CATEGORIES = [
    ('Queijo',     'queijo'),
    ('Café',       'cafe'),
    ('Hortaliças', 'hortalicas'),
    ('Doces',      'doces'),
    ('Leite',      'leite'),
    ('Frutas',     'frutas'),
]


def seed_categories(apps, schema_editor):
    Category = apps.get_model('core', 'Category')
    for name, slug in CATEGORIES:
        Category.objects.get_or_create(slug=slug, defaults={'name': name})


def remove_categories(apps, schema_editor):
    Category = apps.get_model('core', 'Category')
    Category.objects.filter(slug__in=[s for _, s in CATEGORIES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_user_email_token_email_verified_last_seen'),
    ]

    operations = [
        migrations.RunPython(seed_categories, remove_categories),
    ]
