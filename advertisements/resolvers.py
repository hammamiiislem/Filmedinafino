from __future__ import annotations

import uuid
import strawberry
from strawberry.types import Info
from strawberry.file_uploads import Upload
from typing import Optional
from django.db import models
from django.core.exceptions import ValidationError, PermissionDenied

from .models import Advertisement, AdStatus
from .types import (
    AdvertisementType,
    AdMetricsType,
    AdValidationResultType,
    AdStatusEnum,
    CreateAdvertisementInput,
    UpdateAdvertisementInput,
    AdvertisementPayload,
    DeletePayload,
    TrackClickPayload,
)
from .services import AdvertisementService


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de permission
# ─────────────────────────────────────────────────────────────────────────────

def get_partner(info: Info):
    """Vérifie que l'utilisateur est authentifié."""
    user = info.context.request.user
    if not user.is_authenticated:
        raise PermissionError("Authentification requise.")
    return user


def get_admin(info: Info):
    """Vérifie que l'utilisateur est un administrateur (is_staff)."""
    user = info.context.request.user
    if not user.is_authenticated:
        raise PermissionError("Authentification requise.")
    if not user.is_staff:
        raise PermissionError("Accès réservé aux administrateurs.")
    return user


# ─────────────────────────────────────────────────────────────────────────────
# Queries
# ─────────────────────────────────────────────────────────────────────────────

@strawberry.type
class AdvertisementQuery:

    @strawberry.field(description="Liste des publicités du partenaire connecté.")
    def my_advertisements(
        self,
        info: Info,
        status: Optional[AdStatusEnum] = None,
    ) -> list[AdvertisementType]:
        user = get_partner(info)
        qs = Advertisement.objects.filter(user=user)
        if status:
            qs = qs.filter(status=status.value)
        return list(qs)

    @strawberry.field(description="Détail d'une publicité par ID.")
    def advertisement(
        self,
        info: Info,
        id: uuid.UUID,
    ) -> Optional[AdvertisementType]:
        user = get_partner(info)
        try:
            return Advertisement.objects.get(id=id, user=user)
        except Advertisement.DoesNotExist:
            return None

    @strawberry.field(description="Métriques agrégées du partenaire connecté.")
    def ad_metrics(self, info: Info) -> AdMetricsType:
        user = get_partner(info)
        data = AdvertisementService.get_metrics(user)
        return AdMetricsType(**data)

    @strawberry.field(description="[ADMIN] Toutes les publicités, filtrables.")
    def all_advertisements(
        self,
        info: Info,
        status: Optional[AdStatusEnum] = None,
        partner_id: Optional[uuid.UUID] = None,
    ) -> list[AdvertisementType]:
        get_admin(info)
        qs = Advertisement.objects.select_related("user").all()
        if status:
            qs = qs.filter(status=status.value)
        if partner_id:
            qs = qs.filter(user_id=partner_id)
        return list(qs)

    @strawberry.field(description="[ADMIN] Publicités en attente de validation.")
    def pending_validations(self, info: Info) -> list[AdvertisementType]:
        get_admin(info)
        return list(
            Advertisement.objects.filter(
                status__in=[AdStatus.PENDING, AdStatus.REVIEW]
            ).select_related("user").order_by("created_at")
        )

    @strawberry.field(description="Valider un fichier image avant upload (type + taille).")
    def validate_image_file(
        self,
        info: Info,
        file: Upload,
    ) -> AdValidationResultType:
        data = AdvertisementService.validate_file(file)
        return AdValidationResultType(**data)


# ─────────────────────────────────────────────────────────────────────────────
# Mutations
# ─────────────────────────────────────────────────────────────────────────────

@strawberry.type
class AdvertisementMutation:

    # ── Partenaire ────────────────────────────────────────────────────────────

    @strawberry.mutation(description="Créer une publicité. Statut initial : EN ATTENTE.")
    def create_advertisement(
        self,
        info: Info,
        input: CreateAdvertisementInput,
        image: Upload,
    ) -> AdvertisementPayload:
        try:
            user = get_partner(info)
            ad = AdvertisementService.create(
                user=user,
                data=input,
                image=image,
            )
            return AdvertisementPayload(success=True, errors=[], advertisement=ad)
        except (ValidationError, PermissionError, PermissionDenied) as e:
            msgs = e.messages if hasattr(e, "messages") else [str(e)]
            return AdvertisementPayload(success=False, errors=msgs)
        except Exception as e:
            return AdvertisementPayload(success=False, errors=[str(e)])

    @strawberry.mutation(description="Modifier une publicité. Repasse en EN ATTENTE pour re-validation.")
    def update_advertisement(
        self,
        info: Info,
        id: uuid.UUID,
        input: UpdateAdvertisementInput,
        image: Optional[Upload] = None,
    ) -> AdvertisementPayload:
        try:
            user = get_partner(info)
            ad = AdvertisementService.update(
                user=user,
                ad_id=id,
                data=input,
                image=image,
            )
            return AdvertisementPayload(success=True, errors=[], advertisement=ad)
        except (ValidationError, PermissionError, PermissionDenied) as e:
            msgs = e.messages if hasattr(e, "messages") else [str(e)]
            return AdvertisementPayload(success=False, errors=msgs)
        except Exception as e:
            return AdvertisementPayload(success=False, errors=[str(e)])

    @strawberry.mutation(description="Supprimer une publicité (impossible si ACTIVE).")
    def delete_advertisement(
        self,
        info: Info,
        id: uuid.UUID,
    ) -> DeletePayload:
        try:
            user = get_partner(info)
            AdvertisementService.delete(user=user, ad_id=id)
            return DeletePayload(success=True, message="Publicité supprimée.")
        except (PermissionError, PermissionDenied) as e:
            return DeletePayload(success=False, message=str(e))
        except Exception as e:
            return DeletePayload(success=False, message=str(e))

    @strawberry.mutation(description="Mettre en pause une publicité ACTIVE.")
    def pause_advertisement(
        self,
        info: Info,
        id: uuid.UUID,
    ) -> AdvertisementPayload:
        try:
            user = get_partner(info)
            ad = AdvertisementService.set_status(
                user=user,
                ad_id=id,
                new_status=AdStatus.PAUSED,
            )
            return AdvertisementPayload(success=True, errors=[], advertisement=ad)
        except (ValidationError, PermissionError, PermissionDenied) as e:
            msgs = e.messages if hasattr(e, "messages") else [str(e)]
            return AdvertisementPayload(success=False, errors=msgs)

    @strawberry.mutation(description="Reprendre une publicité EN PAUSE.")
    def resume_advertisement(
        self,
        info: Info,
        id: uuid.UUID,
    ) -> AdvertisementPayload:
        try:
            user = get_partner(info)
            ad = AdvertisementService.set_status(
                user=user,
                ad_id=id,
                new_status=AdStatus.ACTIVE,
            )
            return AdvertisementPayload(success=True, errors=[], advertisement=ad)
        except (ValidationError, PermissionError, PermissionDenied) as e:
            msgs = e.messages if hasattr(e, "messages") else [str(e)]
            return AdvertisementPayload(success=False, errors=msgs)

    # ── Admin ─────────────────────────────────────────────────────────────────

    @strawberry.mutation(description="[ADMIN] Approuver une publicité en attente.")
    def approve_advertisement(
        self,
        info: Info,
        id: uuid.UUID,
    ) -> AdvertisementPayload:
        try:
            admin = get_admin(info)
            ad = AdvertisementService.approve(admin_user=admin, ad_id=id)
            return AdvertisementPayload(success=True, errors=[], advertisement=ad)
        except (ValidationError, PermissionError) as e:
            msgs = e.messages if hasattr(e, "messages") else [str(e)]
            return AdvertisementPayload(success=False, errors=msgs)
        except Exception as e:
            return AdvertisementPayload(success=False, errors=[str(e)])

    @strawberry.mutation(description="[ADMIN] Rejeter une publicité avec un motif obligatoire.")
    def reject_advertisement(
        self,
        info: Info,
        id: uuid.UUID,
        reason: str,
    ) -> AdvertisementPayload:
        try:
            admin = get_admin(info)
            ad = AdvertisementService.reject(admin_user=admin, ad_id=id, reason=reason)
            return AdvertisementPayload(success=True, errors=[], advertisement=ad)
        except (ValidationError, PermissionError) as e:
            msgs = e.messages if hasattr(e, "messages") else [str(e)]
            return AdvertisementPayload(success=False, errors=msgs)
        except Exception as e:
            return AdvertisementPayload(success=False, errors=[str(e)])

    # ── Tracking public (sans authentification) ───────────────────────────────

    @strawberry.mutation(description="Enregistrer une impression publicitaire.")
    def track_impression(self, info: Info, id: uuid.UUID) -> bool:
        updated = Advertisement.objects.filter(
            id=id,
            status=AdStatus.ACTIVE,
        ).update(impressions=models.F("impressions") + 1)
        return updated > 0

    @strawberry.mutation(description="Enregistrer un clic et retourner l'URL de redirection.")
    def track_click(self, info: Info, id: uuid.UUID) -> TrackClickPayload:
        try:
            ad = Advertisement.objects.get(id=id, status=AdStatus.ACTIVE)
            Advertisement.objects.filter(id=id).update(
                clicks=models.F("clicks") + 1
            )
            return TrackClickPayload(success=True, redirect_url=ad.redirect_url)
        except Advertisement.DoesNotExist:
            return TrackClickPayload(success=False, redirect_url=None)