import uuid
from django.db import models

class UUIDModel(models.Model):
    """Garantit l'usage de UUID pour empêcher les enumeration attacks"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True

class TimeStampedModel(models.Model):
    """Audit automatique des dates de création et modification"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True