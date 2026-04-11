from __future__ import annotations

import datetime
import strawberry
import strawberry_django
from strawberry import auto
from strawberry.types import Info
from typing import Optional
from django.http import HttpRequest

from .models import Advertisement


# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────

@strawberry.enum
class AdFormatEnum(strawberry.Enum):
    BANNER   = "BANNER"
    SQUARE   = "SQUARE"
    VERTICAL = "VERTICAL"


@strawberry.enum
class AdStatusEnum(strawberry.Enum):
    PENDING  = "PENDING"
    REVIEW   = "REVIEW"
    ACTIVE   = "ACTIVE"
    PAUSED   = "PAUSED"
    REJECTED = "REJECTED"
    EXPIRED  = "EXPIRED"


# ─────────────────────────────────────────────────────────────────────────────
# Type principal
# ─────────────────────────────────────────────────────────────────────────────

@strawberry_django.type(Advertisement)
class AdvertisementType:
    id:               auto
    name:             auto
    redirect_url:     auto
    format:           auto
    status:           auto
    file_type:        auto
    start_date:       auto
    end_date:         auto
    impressions:      auto
    clicks:           auto
    rejection_reason: auto
    reviewed_at:      auto
    created_at:       auto
    updated_at:       auto

    @strawberry_django.field
    def ctr(self, root: Advertisement) -> float:
        """Taux de clic : (clicks / impressions) × 100."""
        if root.impressions == 0:
            return 0.0
        return round((root.clicks / root.impressions) * 100, 2)

    @strawberry_django.field
    def is_active(self, root: Advertisement) -> bool:
        """True si statut ACTIVE et dans la période de diffusion."""
        today = datetime.date.today()
        return (
            root.status == "ACTIVE"
            and root.start_date <= today <= root.end_date
        )

    @strawberry_django.field
    def image_url(self, root: Advertisement, info: Info) -> Optional[str]:
        """URL absolue de l'image."""
        if root.image:
            request: HttpRequest = info.context.request
            return request.build_absolute_uri(root.image.url)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Types métriques & validation
# ─────────────────────────────────────────────────────────────────────────────

@strawberry.type
class AdMetricsType:
    total_impressions: int
    total_clicks:      int
    average_ctr:       float
    active_count:      int
    pending_count:     int


@strawberry.type
class AdValidationResultType:
    valid:     bool
    errors:    list[str]
    file_type: Optional[str]
    file_size: int


# ─────────────────────────────────────────────────────────────────────────────
# Inputs
# ─────────────────────────────────────────────────────────────────────────────

@strawberry.input
class CreateAdvertisementInput:
    name:         str
    redirect_url: str
    format:       AdFormatEnum
    start_date:   datetime.date
    end_date:     datetime.date


@strawberry.input
class UpdateAdvertisementInput:
    name:         Optional[str]           = strawberry.UNSET
    redirect_url: Optional[str]           = strawberry.UNSET
    format:       Optional[AdFormatEnum]  = strawberry.UNSET
    start_date:   Optional[datetime.date] = strawberry.UNSET
    end_date:     Optional[datetime.date] = strawberry.UNSET


# ─────────────────────────────────────────────────────────────────────────────
# Payloads (réponses mutations)
# ─────────────────────────────────────────────────────────────────────────────

@strawberry.type
class AdvertisementPayload:
    success:       bool
    errors:        list[str]
    advertisement: Optional[AdvertisementType] = None


@strawberry.type
class DeletePayload:
    success: bool
    message: str


@strawberry.type
class TrackClickPayload:
    success:      bool
    redirect_url: Optional[str] = None