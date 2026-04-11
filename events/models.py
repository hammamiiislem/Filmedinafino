import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _



class Event(models.Model):
    STATUS_CHOICES = (
        ('PENDING_PAYMENT', _('En attente de paiement')),
        ('PENDING_APPROVAL', _('En attente de validation')),
        ('APPROVED',         _('Approuvé')),
        ('REJECTED',         _('Rejeté')),
    )

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    partner     = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='events_managed')
    title       = models.CharField(max_length=255, verbose_name=_("Title"))
    description = models.TextField(verbose_name=_("Description"))
    start_date  = models.DateTimeField(verbose_name=_("Start Date"))
    end_date    = models.DateTimeField(verbose_name=_("End Date"))
    
    # Media: On garde EventMedia pour le multi-upload, mais on peut ajouter un thumbnail optionnel
    
    registration_link = models.URLField(blank=True, null=True, verbose_name=_("Registration Link"))
    location          = models.ForeignKey('guard.Location', on_delete=models.SET_NULL, null=True, blank=True, related_name='new_events')
    
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING_PAYMENT')
    visibility   = models.BooleanField(default=False, verbose_name=_("Visible onto platforms"))
    is_boosted   = models.BooleanField(default=False, verbose_name=_("Boosted (Top 3)"))
    
    created_at   = models.DateTimeField(auto_now_add=True)
    validated_at = models.DateTimeField(null=True, blank=True)
    
    payment_ref  = models.CharField(max_length=100, blank=True, null=True, unique=True)

    class Meta:
        verbose_name        = _("Event")
        verbose_name_plural = _("Events")
        ordering            = ['-is_boosted', '-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Once approved, lock editing? (Logic logic will be in forms/services)
        if self.status == 'APPROVED' and not self.validated_at:
            from django.utils import timezone
            self.validated_at = timezone.now()
            self.visibility   = True
        super().save(*args, **kwargs)


# 👇 تحطها هنا تحتها مباشرة
class EventMedia(models.Model):
    MEDIA_TYPE = (
        ('IMAGE', 'Image'),
        ('VIDEO', 'Video'),
    )

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='media')
    file = models.FileField(upload_to='events/')
    type = models.CharField(max_length=10, choices=MEDIA_TYPE)

    uploaded_at = models.DateTimeField(auto_now_add=True)