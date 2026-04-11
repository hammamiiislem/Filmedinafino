

import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
import advertisements.models
 
 
class Migration(migrations.Migration):
 
    initial = True
 
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
 
    operations = [
        migrations.CreateModel(
            name="Advertisement",
            fields=[
                ("id",           models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("name",         models.CharField(max_length=200)),
                ("image",        models.ImageField(upload_to=advertisements.models.advertisement_upload_path, validators=[advertisements.models.validate_image_file])),
                ("file_type",    models.CharField(blank=True, editable=False, max_length=10)),
                ("redirect_url", models.URLField(max_length=500)),
                ("format",       models.CharField(choices=[("BANNER","Bannière (728×90)"),("SQUARE","Carré (300×250)"),("VERTICAL","Vertical (160×600)")], default="BANNER", max_length=20)),
                ("status",       models.CharField(choices=[("PENDING","En attente"),("REVIEW","En révision"),("ACTIVE","Active"),("PAUSED","En pause"),("REJECTED","Rejetée"),("EXPIRED","Expirée")], default="PENDING", max_length=20)),
                ("start_date",   models.DateField()),
                ("end_date",     models.DateField()),
                ("impressions",  models.PositiveIntegerField(default=0)),
                ("clicks",       models.PositiveIntegerField(default=0)),
                ("rejection_reason", models.TextField(blank=True)),
                ("reviewed_at",  models.DateTimeField(blank=True, null=True)),
                ("created_at",   models.DateTimeField(auto_now_add=True)),
                ("updated_at",   models.DateTimeField(auto_now=True)),
                ("user",      models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="advertisements", to=settings.AUTH_USER_MODEL)),
                ("reviewed_by",  models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_ads", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"], "verbose_name": "Publicité", "verbose_name_plural": "Publicités"},
        ),
    ]
 


