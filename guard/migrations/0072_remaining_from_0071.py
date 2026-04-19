# Split from original 0071 - handles location partner, LegacyPartner, EmailVerificationToken
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('guard', '0071_guarduser_only'),
        ('partners', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='location',
            name='partner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='owned_locations', to='partners.partner', verbose_name='Partner'),
        ),
        migrations.CreateModel(
            name='EmailVerificationToken',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('token_hash', models.CharField(max_length=64, unique=True)),
                ('expires_at', models.DateTimeField()),
                ('is_used', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='verification_tokens', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LegacyPartner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('email', models.EmailField(blank=True, max_length=254, null=True, unique=True, verbose_name='Email')),
                ('image', models.ImageField(upload_to='partners/', verbose_name='Image')),
                ('link', models.URLField(verbose_name='Link')),
                ('is_verified', models.BooleanField(default=False, verbose_name='Is Verified')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('locations', models.ManyToManyField(blank=True, related_name='legacy_partners', to='guard.location', verbose_name='Locations')),
            ],
            options={
                'verbose_name': 'Partner',
                'verbose_name_plural': 'Partners',
            },
        ),
        migrations.DeleteModel(
            name='Partner',
        ),
    ]