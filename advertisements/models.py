import os
import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_image_file(value):
    """Valide le type et la taille du fichier image."""
    ext = os.path.splitext(value.name)[1].lower()
    allowed_extensions = ['.gif', '.png', '.jpg', '.jpeg']
    if ext not in allowed_extensions:
        raise ValidationError(
            f"Format non supporté '{ext}'. Formats acceptés : GIF, PNG, JPG."
        )
    if hasattr(value, 'size') and value.size > 2 * 1024 * 1024:
        raise ValidationError("La taille du fichier ne doit pas dépasser 2 Mo.")


def advertisement_upload_path(instance, filename):
    """Génère un chemin d'upload unique par partenaire."""
    ext = os.path.splitext(filename)[1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    return f"advertisements/user_{instance.user_id}/{unique_name}"


class AdFormat(models.TextChoices):
    BANNER     = 'BANNER',   'Bannière (728×90)'
    SQUARE     = 'SQUARE',   'Carré (300×250)'
    VERTICAL   = 'VERTICAL', 'Vertical (160×600)'


class AdStatus(models.TextChoices):
    PENDING  = 'PENDING',  'En attente de validation'
    REVIEW   = 'REVIEW',   'En révision'
    ACTIVE   = 'ACTIVE',   'Active'
    PAUSED   = 'PAUSED',   'En pause'
    REJECTED = 'REJECTED', 'Rejetée'
    EXPIRED  = 'EXPIRED',  'Expirée'


class Advertisement(models.Model):
    # ── Identité ──────────────────────────────────────────────────────────────
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='advertisements'
    )
    name        = models.CharField(max_length=200, verbose_name="Nom de la publicité")

    # ── Fichier image ─────────────────────────────────────────────────────────
    image       = models.ImageField(
        upload_to=advertisement_upload_path,
        validators=[validate_image_file],
        verbose_name="Image / GIF"
    )
    file_type   = models.CharField(max_length=10, editable=False)   # GIF | PNG | JPG

    # ── Redirection ───────────────────────────────────────────────────────────
    redirect_url = models.URLField(max_length=500, verbose_name="URL de redirection")

    # ── Format & statut ───────────────────────────────────────────────────────
    format      = models.CharField(
        max_length=20,
        choices=AdFormat.choices,
        default=AdFormat.BANNER
    )
    status      = models.CharField(
        max_length=20,
        choices=AdStatus.choices,
        default=AdStatus.PENDING
    )

    # ── Période de diffusion ──────────────────────────────────────────────────
    start_date  = models.DateField(verbose_name="Date de début")
    end_date    = models.DateField(verbose_name="Date de fin")

    # ── Métriques (mises à jour asynchronement) ───────────────────────────────
    impressions = models.PositiveIntegerField(default=0)
    clicks      = models.PositiveIntegerField(default=0)

    # ── Validation admin ──────────────────────────────────────────────────────
    reviewed_by     = models.ForeignKey(
        'auth.User',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_ads'
    )
    reviewed_at     = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Publicité"
        verbose_name_plural = "Publicités"

    def __str__(self):
        return f"[{self.user}] {self.name} ({self.status})"

    def save(self, *args, **kwargs):
        # Détecter automatiquement le type de fichier
        if self.image:
            ext = os.path.splitext(self.image.name)[1].upper().lstrip('.')
            self.file_type = 'JPG' if ext == 'JPEG' else ext
        # Vérifier l'expiration automatique
        if self.end_date and self.end_date < timezone.now().date():
            self.status = AdStatus.EXPIRED
        super().save(*args, **kwargs)

    @property
    def ctr(self):
        """Taux de clic (Click-Through Rate)."""
        if self.impressions == 0:
            return 0.0
        return round((self.clicks / self.impressions) * 100, 2)

    @property
    def is_active(self):
        today = timezone.now().date()
        return (
            self.status == AdStatus.ACTIVE
            and self.start_date <= today <= self.end_date
        )