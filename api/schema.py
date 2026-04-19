import strawberry
import strawberry_django
from strawberry import auto
from typing import List, Optional
import math
import datetime
import uuid
from django.utils import timezone
from django.conf import settings
import guard.schema
import partners.schema

# GraphQL specific imports
from graphql.validation import NoSchemaIntrospectionCustomRule
from strawberry.extensions import AddValidationRules
from strawberry.file_uploads import Upload

# Models imports (Nadhamthom f-makan wa7ed)
from cities_light.models import City, Country
from shared.models import Page, UserPreference
from guard.models import (
    Location,
    LocationCategory,
    Hiking,
    HikingLocation,
    Event,
    EventCategory,
    Ad,
    AdClick,
    EventClick,
    Tip,
    PublicTransport,
    PublicTransportType,
    PublicTransportTime,
    ImageLocation,
    ImageHiking,
    ImageEvent,
    ImageAd,
    LegacyPartner,
    Sponsor,
    Weekday,
    ArHistoricalContent,
)
from partners.models import Partner

# Utils w Resolvers
from shared.utils import send_validation_email
from events.resolvers import Query as EventQuery, Mutation as EventMutation

from guard.schema import Mutation as GuardMutation
from partners.schema import Mutation as PartnerMutation, Query as PartnerQuery


@strawberry.type
class ImageFieldType:
    @strawberry.field
    def url(self, info:str, root) -> str:
        if not root:
            return ""
        try:
            return info.context.request.build_absolute_uri(root.url)
        except Exception:
            return root.url

    @strawberry.field
    def name(self, root) -> str:
        return root.name if root else ""

    @strawberry.field
    def path(self, root) -> str:
        return root.path if root and hasattr(root, "path") else ""

    @strawberry.field
    def size(self, root) -> int:
        return root.size if root and hasattr(root, "size") else 0

    @strawberry.field
    def width(self, root) -> Optional[int]:
        try:
            return root.width if root and hasattr(root, "width") else None
        except Exception:
            return None

    @strawberry.field
    def height(self, root) -> Optional[int]:
        try:
            return root.height if root and hasattr(root, "height") else None
        except Exception:
            return None


@strawberry_django.type(Page)
class PageType:
    id: auto
    slug: auto
    slug_en: str
    slug_fr: str
    is_active: auto
    created_at: auto
    updated_at: auto
    title: auto
    title_en: str
    title_fr: str
    content: str
    content_en: str
    content_fr: str


@strawberry_django.type(Weekday)
class WeekdayType:
    id: auto
    day: auto


from partners.schema import PartnerType

@strawberry_django.type(Sponsor)
class SponsorType:
    id: auto
    name: auto
    link: auto

    @strawberry.field
    def image(self, root) -> ImageFieldType:
        return root.image


@strawberry_django.type(ImageLocation)
class ImageLocationType:
    id: auto
    created_at: auto

    @strawberry.field
    def image(self, root) -> ImageFieldType:
        return root.image

    @strawberry.field(name="imageMobile")
    def image_mobile(self, root) -> Optional[ImageFieldType]:
        return root.image_mobile


@strawberry_django.type(LocationCategory)
class LocationCategoryType:
    id: auto
    name: auto
    name_en: str
    name_fr: str
    created_at: auto
    updated_at: auto


@strawberry_django.type(ArHistoricalContent)
class ArHistoricalContentType:
    id: auto
    name: auto
    description: auto
    is_active: auto
    created_at: auto

    @strawberry.field
    def marker_image(self, root) -> ImageFieldType:
        return root.marker_image

    @strawberry.field
    def historical_asset(self, root) -> ImageFieldType:
        return root.historical_asset


@strawberry_django.type(Location)
class LocationType:
    id: auto
    created_at: auto
    name: auto
    name_en: str
    name_fr: str
    longitude: auto
    latitude: auto
    is_active_ads: auto
    story: str
    story_en: str
    story_fr: str
    open_from: auto = strawberry_django.field(field_name="openFrom") # Hna 5alliha openFrom khater fil model maktouba haka
    open_to: auto = strawberry_django.field(field_name="openTo")
    admission_fee: auto = strawberry_django.field(field_name="admissionFee")
    city: Optional["CityType"]
    category: Optional[LocationCategoryType]
    partner: Optional['PartnerType']

    @strawberry.field
    def images(self, root) -> List[ImageLocationType]:
        return root.images.all()

    @strawberry.field
    def closed_days(self, root) -> List[WeekdayType]:
        return root.closedDays.all()

    @strawberry.field
    def ar_contents(self, root) -> List[ArHistoricalContentType]:
        return root.ar_contents.filter(is_active=True)


@strawberry_django.type(ImageHiking)
class ImageHikingType:
    id: auto
    created_at: auto

    @strawberry.field
    def image(self, root) -> ImageFieldType:
        return root.image

    @strawberry.field(name="imageMobile")
    def image_mobile(self, root) -> Optional[ImageFieldType]:
        return root.image_mobile


@strawberry_django.type(HikingLocation)
class HikingLocationType:
    order: auto
    location: "LocationType"


@strawberry_django.type(Hiking)
class HikingType:
    id: auto
    created_at: auto
    updated_at: auto
    name: auto
    name_en: str
    name_fr: str
    description: auto
    description_en: str
    description_fr: str
    city: Optional["CityType"]

    latitude: Optional[float]
    longitude: Optional[float]

    @strawberry.field
    def images(self, root) -> List[ImageHikingType]:
        return root.images.all()

    @strawberry.field
    def locations(self, root) -> List[HikingLocationType]:
        # Fetch directly from the through model to get the 'order' field
        return root.hikinglocation_set.all().order_by("order")


@strawberry_django.type(EventCategory)
class EventCategoryType:
    id: auto
    name: auto
    name_en: str
    name_fr: str
    created_at: auto
    updated_at: auto


@strawberry_django.type(ImageEvent)
class ImageEventType:
    id: auto
    created_at: auto

    @strawberry.field
    def image(self, root) -> ImageFieldType:
        return root.image

    @strawberry.field(name="imageMobile")
    def image_mobile(self, root) -> Optional[ImageFieldType]:
        return root.image_mobile


@strawberry_django.type(Event)
class EventType:
    id: auto
    created_at: auto
    name: auto
    name_en: str
    name_fr: str
    start_date: auto = strawberry_django.field(field_name="startDate")
    end_date: auto = strawberry_django.field(field_name="endDate")
    time: auto
    price: auto
    link: auto
    short_link: auto
    short_id: auto
    boost: auto
    description: str
    description_en: str
    description_fr: str
    city: Optional["CityType"]
    category: Optional[EventCategoryType]
    location: Optional[LocationType]

    @strawberry.field
    def images(self, root) -> List[ImageEventType]:
        return root.images.all()


@strawberry_django.type(ImageAd)
class ImageAdType:
    id: auto
    created_at: auto

    @strawberry.field
    def image(self, root) -> ImageFieldType:
        return root.image

    @strawberry.field(name="imageMobile")
    def image_mobile(self, root) -> Optional[ImageFieldType]:
        return root.image_mobile


@strawberry_django.type(Country)
class CountryType:
    id: auto
    name: auto
    code2: auto
    code3: auto


@strawberry_django.type(Ad)
class AdType:
    id: auto
    created_at: auto
    updated_at: auto
    name: auto
    link: auto
    short_link: auto
    short_id: auto
    clicks: auto
    is_active: auto
    country: Optional[CountryType]
    city: Optional["CityType"]

    @strawberry.field(name="imageMobile")
    def image_mobile(self, root) -> Optional[ImageFieldType]:
        return root.image_mobile

    @strawberry.field(name="imageTablet")
    def image_tablet(self, root) -> Optional[ImageFieldType]:
        return root.image_tablet

    @strawberry.field
    def images(self, root) -> List[ImageAdType]:
        return root.images.all() if hasattr(root, "images") else []


@strawberry_django.type(Tip)
class TipType:
    id: auto
    created_at: auto
    updated_at: auto
    description: str
    description_en: str
    description_fr: str
    city: Optional["CityType"]


@strawberry_django.type(City)
class CityType:
    id: auto
    name: auto

    @strawberry.field
    def name_en(self, root) -> Optional[str]:
        # root.translations is a dict like {'en': ['Name'], ...}
        translations = getattr(root, "translations", {})
        en_names = translations.get("en", [])
        return en_names[0] if en_names else root.name

    @strawberry.field
    def name_fr(self, root) -> Optional[str]:
        translations = getattr(root, "translations", {})
        fr_names = translations.get("fr", [])
        return fr_names[0] if fr_names else root.name

    @strawberry.field
    def name_ar(self, root) -> Optional[str]:
        translations = getattr(root, "translations", {})
        ar_names = translations.get("ar", [])
        return ar_names[0] if ar_names else root.name

    @strawberry.field
    def region(self, root) -> Optional[str]:
        return root.region.name if hasattr(root, "region") and root.region else None

    @strawberry.field
    def region_en(self, root) -> Optional[str]:
        if not hasattr(root, "region") or not root.region:
            return None
        translations = getattr(root.region, "translations", {})
        en_names = translations.get("en", [])
        return en_names[0] if en_names else root.region.name

    @strawberry.field
    def region_fr(self, root) -> Optional[str]:
        if not hasattr(root, "region") or not root.region:
            return None
        translations = getattr(root.region, "translations", {})
        fr_names = translations.get("fr", [])
        return fr_names[0] if fr_names else root.region.name

    @strawberry.field
    def region_ar(self, root) -> Optional[str]:
        if not hasattr(root, "region") or not root.region:
            return None
        translations = getattr(root.region, "translations", {})
        ar_names = translations.get("ar", [])
        return ar_names[0] if ar_names else root.region.name

    @strawberry.field
    def country(self, root) -> Optional[str]:
        return root.country.name if hasattr(root, "country") and root.country else None

    @strawberry.field
    def country_en(self, root) -> Optional[str]:
        if not hasattr(root, "country") or not root.country:
            return None
        translations = getattr(root.country, "translations", {})
        en_names = translations.get("en", [])
        return en_names[0] if en_names else root.country.name

    @strawberry.field
    def country_fr(self, root) -> Optional[str]:
        if not hasattr(root, "country") or not root.country:
            return None
        translations = getattr(root.country, "translations", {})
        fr_names = translations.get("fr", [])
        return fr_names[0] if fr_names else root.country.name

    @strawberry.field
    def country_ar(self, root) -> Optional[str]:
        if not hasattr(root, "country") or not root.country:
            return None
        translations = getattr(root.country, "translations", {})
        ar_names = translations.get("ar", [])
        return ar_names[0] if ar_names else root.country.name


@strawberry_django.type(PublicTransportType)
class PublicTransportTypeType:
    id: auto
    name: auto
    name_en: str
    name_fr: str


@strawberry_django.type(PublicTransportTime)
class PublicTransportTimeType:
    id: auto
    created_at: auto
    updated_at: auto
    time: auto


@strawberry_django.type(PublicTransport)
class PublicTransportNodeType:
    id: auto
    created_at: auto
    updated_at: auto
    city: Optional[CityType]
    from_city: Optional[CityType] = strawberry_django.field(field_name="fromCity")
    to_city: Optional[CityType] = strawberry_django.field(field_name="toCity")
    bus_number: auto = strawberry_django.field(field_name="busNumber")

    @strawberry.field
    def public_transport_type(self, root) -> Optional[PublicTransportTypeType]:
        return root.publicTransportType

    @strawberry.field
    def from_region(self, root) -> Optional[str]:
        return root.fromRegion.name if root.fromRegion else None

    @strawberry.field
    def from_region_en(self, root) -> Optional[str]:
        if not root.fromRegion:
            return None
        translations = getattr(root.fromRegion, "translations", {})
        names = translations.get("en", [])
        return names[0] if names else root.fromRegion.name

    @strawberry.field
    def from_region_fr(self, root) -> Optional[str]:
        if not root.fromRegion:
            return None
        translations = getattr(root.fromRegion, "translations", {})
        names = translations.get("fr", [])
        return names[0] if names else root.fromRegion.name

    @strawberry.field
    def from_region_ar(self, root) -> Optional[str]:
        if not root.fromRegion:
            return None
        translations = getattr(root.fromRegion, "translations", {})
        names = translations.get("ar", [])
        return names[0] if names else root.fromRegion.name

    @strawberry.field
    def to_region(self, root) -> Optional[str]:
        return root.toRegion.name if root.toRegion else None

    @strawberry.field
    def to_region_en(self, root) -> Optional[str]:
        if not root.toRegion:
            return None
        translations = getattr(root.toRegion, "translations", {})
        names = translations.get("en", [])
        return names[0] if names else root.toRegion.name

    @strawberry.field
    def to_region_fr(self, root) -> Optional[str]:
        if not root.toRegion:
            return None
        translations = getattr(root.toRegion, "translations", {})
        names = translations.get("fr", [])
        return names[0] if names else root.toRegion.name

    @strawberry.field
    def to_region_ar(self, root) -> Optional[str]:
        if not root.toRegion:
            return None
        translations = getattr(root.toRegion, "translations", {})
        names = translations.get("ar", [])
        return names[0] if names else root.toRegion.name

    @strawberry.field
    def times(self, root) -> List[PublicTransportTimeType]:
        return root.publicTransportTimes.all()


@strawberry.type
class Query(
    EventQuery, 
    PartnerQuery, # ✅ Ajout de la gestion des partenaires
):
    @strawberry.field
    def pages(self, is_active: Optional[bool] = None) -> List[PageType]:
        qs = Page.objects.all()
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        return qs

    @strawberry.field
    def page(self, slug: str) -> Optional[PageType]:
        return (
            Page.objects.filter(Q(slug_en=slug) | Q(slug_fr=slug))
            .filter(is_active=True)
            .first()
        )

    @strawberry.field
    def locations(
        self,
        city_id: Optional[int] = None,
        category_id: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = 0,
    ) -> List[LocationType]:
        qs = Location.objects.select_related(
            "city", "country", "category"
        ).prefetch_related("images")
        if city_id is not None:
            qs = qs.filter(city_id=city_id)
        if category_id is not None:
            qs = qs.filter(category_id=category_id)

        if limit is not None:
            qs = qs[offset : offset + limit]

        return qs

    @strawberry.field
    def location(self, id: strawberry.ID) -> Optional[LocationType]:
        return Location.objects.prefetch_related("images").filter(pk=id).first()

    @strawberry.field
    def location_categories(self) -> List[LocationCategoryType]:
        return LocationCategory.objects.all()

    @strawberry.field
    def hikings(
        self,
        city_id: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = 0,
    ) -> List[HikingType]:
        qs = Hiking.objects.select_related("city").prefetch_related(
            "images", "locations"
        )
        if city_id is not None:
            qs = qs.filter(city_id=city_id)

        if limit is not None:
            qs = qs[offset : offset + limit]

        return qs

    @strawberry.field
    def hiking(self, id: strawberry.ID) -> Optional[HikingType]:
        return (
            Hiking.objects.prefetch_related("images", "locations").filter(pk=id).first()
        )

    @strawberry.field
    def events(
        self,
        city_id: Optional[int] = None,
        category_id: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = 0,
        boost: Optional[bool] = None,
    ) -> List[EventType]:
        qs = Event.objects.select_related(
            "city", "category", "client", "location"
        ).prefetch_related("images")
        if city_id is not None:
            qs = qs.filter(city_id=city_id)
        if category_id is not None:
            qs = qs.filter(category_id=category_id)
        if boost is not None:
            qs = qs.filter(boost=boost)

        # Filter out expired events (keep for 1 day after ending)
        yesterday = timezone.now().date() - datetime.timedelta(days=1)
        qs = qs.filter(endDate__gte=yesterday)

        if limit is not None:
            qs = qs[offset : offset + limit]

        return qs

    @strawberry.field
    def event(self, id: strawberry.ID) -> Optional[EventType]:
        return (
            Event.objects.prefetch_related("images", "location", "category")
            .filter(pk=id)
            .first()
        )

    @strawberry.field
    def event_categories(self) -> List[EventCategoryType]:
        return EventCategory.objects.all()

    @strawberry.field
    def ads(
        self,
        city_id: Optional[int] = None,
        country_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = 0,
    ) -> List[AdType]:
        qs = Ad.objects.select_related("city", "country", "client")
        if city_id is not None:
            qs = qs.filter(city_id=city_id)
        if country_id is not None:
            qs = qs.filter(country_id=country_id)
        if is_active is not None:
            qs = qs.filter(is_active=is_active)

        if limit is not None:
            qs = qs[offset : offset + limit]

        return qs

    @strawberry.field
    def ad(self, id: strawberry.ID) -> Optional[AdType]:
        return Ad.objects.filter(pk=id).first()

    @strawberry.field
    def tips(
        self,
        city_id: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = 0,
    ) -> List[TipType]:
        qs = Tip.objects.select_related("city")
        if city_id is not None:
            qs = qs.filter(city_id=city_id)

        if limit is not None:
            qs = qs[offset : offset + limit]

        return qs

    @strawberry.field
    def public_transports(
        self,
        city_id: Optional[int] = None,
        type_id: Optional[int] = None,
        from_region_id: Optional[int] = None,
        to_region_id: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = 0,
    ) -> List[PublicTransportNodeType]:
        qs = PublicTransport.objects.select_related(
            "city", "publicTransportType", "fromRegion", "toRegion"
        ).prefetch_related("publicTransportTimes")
        if city_id is not None:
            qs = qs.filter(city_id=city_id)
        if type_id is not None:
            qs = qs.filter(publicTransportType_id=type_id)
        if from_region_id is not None:
            qs = qs.filter(fromRegion_id=from_region_id)
        if to_region_id is not None:
            qs = qs.filter(toRegion_id=to_region_id)

        if limit is not None:
            qs = qs[offset : offset + limit]

        return qs

    @strawberry.field
    def public_transport(self, id: strawberry.ID) -> Optional[PublicTransportNodeType]:
        return (
            PublicTransport.objects.select_related(
                "city", "publicTransportType", "fromRegion", "toRegion"
            )
            .prefetch_related("publicTransportTimes")
            .filter(pk=id)
            .first()
        )

    @strawberry.field
    def public_transport_types(self) -> List[PublicTransportTypeType]:
        return PublicTransportType.objects.all()

    @strawberry.field
    def nearest_city(
        self, lat: float, lon: float, max_distance_km: Optional[float] = None
    ) -> Optional[CityType]:
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371  # Earth radius in km
            phi1 = math.radians(lat1)
            phi2 = math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlambda = math.radians(lon2 - lon1)
            a = (
                math.sin(dphi / 2) ** 2
                + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
            )
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            return R * c

        candidates = (
            City.objects.exclude(latitude__isnull=True)
            .exclude(longitude__isnull=True)
            .values("id", "name", "latitude", "longitude")
        )

        nearest = None
        nearest_distance = None

        for city in candidates:
            distance = haversine(
                lat, lon, float(city["latitude"]), float(city["longitude"])
            )
            if max_distance_km is not None and distance > max_distance_km:
                continue
            if nearest_distance is None or distance < nearest_distance:
                nearest_distance = distance
                nearest = city["id"]

        if nearest is None:
            return None

        return City.objects.filter(pk=nearest).first()

    @strawberry.field
    def partners(self) -> List[PartnerType]:
        return Partner.objects.all()

    @strawberry.field
    def sponsor(self, id: strawberry.ID) -> Optional[SponsorType]:
        return Sponsor.objects.filter(pk=id).first()

    @strawberry.field
    def sponsors(self) -> List[SponsorType]:
        return Sponsor.objects.all()


@strawberry.type
class SyncUserPreferencePayload:
    ok: bool


@strawberry.type
class RegisterDevicePayload:
    ok: bool
    message: Optional[str] = None


@strawberry.type
class Mutation(EventMutation, GuardMutation, PartnerMutation):
    @strawberry.mutation
    def sync_user_preference(
        self,
        user_uid: uuid.UUID,
        first_visit: bool,
        traveling_with: str,
        interests: List[str],
        updated_at: datetime.datetime,
    ) -> SyncUserPreferencePayload:
        obj, created = UserPreference.objects.get_or_create(
            user_uid=user_uid,
            defaults={
                "first_visit": first_visit,
                "traveling_with": traveling_with,
                "interests": interests,
                "updated_at": updated_at,
            },
        )

        if not created and updated_at > obj.updated_at:
            obj.first_visit = first_visit
            obj.traveling_with = traveling_with
            obj.interests = interests
            obj.save()

        return SyncUserPreferencePayload(ok=True)

    @strawberry.mutation
    def forget_me(self, user_uid: uuid.UUID) -> SyncUserPreferencePayload:
        UserPreference.objects.filter(user_uid=user_uid).delete()
        return SyncUserPreferencePayload(ok=True)

    @strawberry.mutation
    def register_fcm_device(
        self,
        registration_id: str,
        type: str,  # 'android' or 'ios'
        name: Optional[str] = None,
        user_uid: Optional[uuid.UUID] = None,
    ) -> RegisterDevicePayload:
        """
        Register an FCM device token for push notifications.

        Args:
            registration_id: FCM token from the mobile app
            type: Device type - 'android' or 'ios'
            name: Optional device name/identifier
            user_uid: Optional user UUID to associate device with user
        """
        try:
            from fcm_django.models import FCMDevice

            # Validate device type
            if type not in ["android", "ios", "web"]:
                return RegisterDevicePayload(
                    ok=False,
                    message=f"Invalid device type: {type}. Must be 'android', 'ios', or 'web'",
                )

            # Get or create device
            device, created = FCMDevice.objects.get_or_create(
                registration_id=registration_id,
                defaults={
                    "type": type,
                    "name": name or f"{type} device",
                    "active": True,
                },
            )

            # Update if device already exists
            if not created:
                device.type = type
                device.active = True
                if name:
                    device.name = name
                device.save()

            # Optionally associate with user if user_uid provided
            if user_uid:
                try:
                    user_pref = UserPreference.objects.get(user_uid=user_uid)
                    # Note: FCMDevice.user is a ForeignKey to User model
                    # If you want to associate with UserPreference, you'd need to adjust this
                    # For now, we just store the registration_id
                    pass
                except UserPreference.DoesNotExist:
                    pass

            return RegisterDevicePayload(
                ok=True,
                message="Device registered successfully"
                if created
                else "Device updated successfully",
            )

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Error registering FCM device: {e}", exc_info=True)
            return RegisterDevicePayload(
                ok=False, message=f"Error registering device: {str(e)}"
            )

    @strawberry.mutation
    def record_ad_click(self, ad_id: strawberry.ID) -> bool:
        # ... logic ...
        return True # Simplified for now

    @strawberry.mutation
    def record_event_click(self, event_id: strawberry.ID) -> bool:
        # ... logic ...
        return True

# --- HNA EL SOLUTION: Lezem el variables héthom ykounou L-BARRA mel class Mutation ---

extensions = []

if not settings.DEBUG:
    from graphql.validation import NoSchemaIntrospectionCustomRule
    # On ajoute la règle de sécurité pour la production
    extensions.append(strawberry.extensions.AddValidationRules([NoSchemaIntrospectionCustomRule]))

# Enfin, on définit le schema
schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=extensions)