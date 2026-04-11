from django.core.exceptions import ValidationError, PermissionDenied
import strawberry

from django.utils import timezone
from django.db import models
from .models import Advertisement, AdStatus
import os


class AdvertisementService:

    @staticmethod
    def get_metrics(user):
        """Calcule les métriques agrégées pour un partenaire (user)."""
        ads = Advertisement.objects.filter(user=user)
        return {
            "total_ads": ads.count(),
            "active_ads": ads.filter(status=AdStatus.ACTIVE).count(),
            "total_impressions": ads.aggregate(total=models.Sum("impressions"))["total"] or 0,
            "total_clicks": ads.aggregate(total=models.Sum("clicks"))["total"] or 0,
        }

    @staticmethod
    def validate_file(file):
        """Simulation de validation de fichier (utilisée par GraphQL)."""
        ext = os.path.splitext(file.name)[1].lower()
        is_valid = ext in ['.gif', '.png', '.jpg', '.jpeg']
        return {
            "is_valid": is_valid,
            "message": "Fichier valide" if is_valid else "Format non supporté (GIF, PNG, JPG uniquement)",
        }

    @staticmethod
    def create(user, data, image):
        """Crée une nouvelle publicité."""
        # data est un CreateAdvertisementInput
        ad = Advertisement(
            user=user,
            name=data.name,
            image=image,
            redirect_url=data.redirect_url,
            format=data.format,
            start_date=data.start_date,
            end_date=data.end_date,
            status=AdStatus.PENDING
        )
        ad.full_clean()
        ad.save()
        return ad

    @staticmethod
    def update(user, ad_id, data, image=None):
        """Met à jour une publicité existante."""
        try:
            ad = Advertisement.objects.get(id=ad_id, user=user)
        except Advertisement.DoesNotExist:
            raise PermissionDenied("Publicité non trouvée ou accès refusé.")

        # Update fields from data (UpdateAdvertisementInput)
        for field in ["name", "redirect_url", "format", "start_date", "end_date"]:
            val = getattr(data, field)
            if val is not strawberry.UNSET:
                setattr(ad, field, val)

        if image:
            ad.image = image

        # Toute modification repasse en attente de validation
        ad.status = AdStatus.PENDING
        ad.full_clean()
        ad.save()
        return ad

    @staticmethod
    def delete(user, ad_id):
        """Supprime une publicité si elle n'est pas active."""
        try:
            ad = Advertisement.objects.get(id=ad_id, user=user)
        except Advertisement.DoesNotExist:
            raise PermissionDenied("Publicité non trouvée.")

        if ad.status == AdStatus.ACTIVE:
            raise ValidationError("Impossible de supprimer une publicité active.")

        ad.delete()
        return True

    @staticmethod
    def set_status(user, ad_id, new_status):
        """Change le statut (PAUSE/ACTIVE) si autorisé."""
        try:
            ad = Advertisement.objects.get(id=ad_id, user=user)
        except Advertisement.DoesNotExist:
            raise PermissionDenied("Publicité non trouvée.")

        if new_status == AdStatus.PAUSED and ad.status != AdStatus.ACTIVE:
            raise ValidationError("Seule une publicité active peut être mise en pause.")
        if new_status == AdStatus.ACTIVE and ad.status != AdStatus.PAUSED:
            raise ValidationError("Seule une publicité en pause peut être reprise.")

        ad.status = new_status
        ad.save(update_fields=['status'])
        return ad

    @staticmethod
    def approve(admin_user, ad_id):
        """[ADMIN] Approuve une publicité."""
        ad = Advertisement.objects.get(id=ad_id)
        ad.status = AdStatus.ACTIVE
        ad.reviewed_by = admin_user
        ad.reviewed_at = timezone.now()
        ad.save()
        return ad

    @staticmethod
    def reject(admin_user, ad_id, reason):
        """[ADMIN] Rejette une publicité avec un motif."""
        ad = Advertisement.objects.get(id=ad_id)
        ad.status = AdStatus.REJECTED
        ad.reviewed_by = admin_user
        ad.reviewed_at = timezone.now()
        ad.rejection_reason = reason
        ad.save()
        return ad