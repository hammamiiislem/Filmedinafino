from django.db import migrations

def fix_categories(apps, schema_editor):
    LocationCategory = apps.get_model('guard', 'LocationCategory')
    
    # We clear the table to ensure we have exactly what's requested
    LocationCategory.objects.all().delete()

    categories = [
        ("Musée", "Museum"),
        ("Restaurant", "Restaurant"),
        ("Hôtel", "Hotel"),
        ("Plage", "Beach"),
        ("Parc", "Park"),
        ("Monument", "Monument"),
        ("Shopping", "Shopping"),
        ("Sport", "Sport"),
        ("Café", "Cafe"),
        ("Autre", "Other"),
    ]

    for fr_name, en_name in categories:
        # Since modeltranslation is active, we set both fields
        LocationCategory.objects.create(name_fr=fr_name, name_en=en_name)

class Migration(migrations.Migration):

    dependencies = [
        ('guard', '0066_merge_20260401_1041'),
    ]

    operations = [
        migrations.RunPython(fix_categories),
    ]
