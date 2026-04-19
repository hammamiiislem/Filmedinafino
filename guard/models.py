import os
import uuid

from django.db import models
from django.db.models.signals import post_delete
from django.db.models import FileField
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from tinymce.models import HTMLField
from django.core.files.uploadedfile import UploadedFile
from shared.models import OptimizedImageModel, UserProfile
from shared.utils import optimize_image, resize_to_fixed
import hashlib
from core.models import UUIDModel, TimeStampedModel
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import CustomUserManager

from django.contrib.auth import get_user_model


# =============================================================================
# CLICK (modèle générique)
# =============================================================================
class Click(models.Model):
    TYPE_CHOICES = (
        ('ad',    'Ad'),
        ('event', 'Event'),
    )
    type       = models.CharField(max_length=10, choices=TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)


# =============================================================================
# CHEMINS D'UPLOAD
# =============================================================================
def location_image_path(instance, filename):
    name, ext = os.path.splitext(filename)
    return f"locations/{instance.location.id}/{name}.jpg"

def ar_marker_path(instance, filename):
    return f"ar/markers/{instance.location.id}/{filename}"

def ar_asset_path(instance, filename):
    return f"ar/assets/{instance.location.id}/{filename}"

def event_image_path(instance, filename):
    name, ext = os.path.splitext(filename)
    return f"events/{instance.event.id}/{name}.jpg"

def hiking_image_path(instance, filename):
    name, ext = os.path.splitext(filename)
    return f"hikings/{instance.hiking.id}/{name}.jpg"

def ad_image_path(instance, filename):
    name, ext = os.path.splitext(filename)
    return f"ads/{instance.ad.id}/{name}.jpg"


# =============================================================================
# AR HISTORICAL CONTENT
# =============================================================================
class ArHistoricalContent(models.Model):
    location         = models.ForeignKey("guard.Location", on_delete=models.CASCADE, related_name="ar_contents")
    name             = models.CharField(_("Name"), max_length=255)
    marker_image     = models.ImageField(upload_to=ar_marker_path, verbose_name=_("Marker Image (The real world target)"), help_text=_("Image representing the real world site for recognition"))
    historical_asset = models.FileField(upload_to=ar_asset_path, verbose_name=_("3D Model or Historical Overlay"), help_text=_(".glb or .usdz file containing the historical reconstruction"))
    description      = models.TextField(_("Historical Description"), blank=True)
    is_active        = models.BooleanField(default=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = _("AR Historical Content")
        verbose_name_plural = _("AR Historical Contents")

    def __str__(self):
        return f"AR: {self.name} ({self.location.name})"


# =============================================================================
# IMAGES (OptimizedImageModel)
# =============================================================================
class ImageAd(OptimizedImageModel):
    ad = models.ForeignKey("guard.Ad", on_delete=models.CASCADE, related_name="images")

    class Meta:
        verbose_name        = _("Ad Image")
        verbose_name_plural = _("Ad Images")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._meta.get_field("image").upload_to        = ad_image_path
        self._meta.get_field("image_mobile").upload_to = ad_image_path


class ImageHiking(OptimizedImageModel):
    hiking = models.ForeignKey("guard.Hiking", on_delete=models.CASCADE, related_name="images")

    class Meta:
        verbose_name        = _("Hiking Image")
        verbose_name_plural = _("Hiking Images")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._meta.get_field("image").upload_to        = hiking_image_path
        self._meta.get_field("image_mobile").upload_to = hiking_image_path


class ImageLocation(OptimizedImageModel):
    location = models.ForeignKey("guard.Location", on_delete=models.CASCADE, related_name="images")

    class Meta:
        verbose_name        = _("Location Image")
        verbose_name_plural = _("Location Images")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._meta.get_field("image").upload_to        = location_image_path
        self._meta.get_field("image_mobile").upload_to = location_image_path


class ImageEvent(OptimizedImageModel):
    event = models.ForeignKey("guard.Event", on_delete=models.CASCADE, related_name="images")

    class Meta:
        verbose_name        = _("Event Image")
        verbose_name_plural = _("Event Images")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._meta.get_field("image").upload_to        = event_image_path
        self._meta.get_field("image_mobile").upload_to = event_image_path


# =============================================================================
# LOCATION
# =============================================================================
class LocationCategory(models.Model):
    name       = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = _("Location Category")
        verbose_name_plural = _("Location Categories")

    def __str__(self):
        return self.name


class WeekdayChoices(models.IntegerChoices):
    SUNDAY    = 1, _("Sunday")
    MONDAY    = 2, _("Monday")
    TUESDAY   = 3, _("Tuesday")
    WEDNESDAY = 4, _("Wednesday")
    THURSDAY  = 5, _("Thursday")
    FRIDAY    = 6, _("Friday")
    SATURDAY  = 7, _("Saturday")

class Weekday(models.Model):
    day = models.IntegerField(choices=WeekdayChoices.choices, unique=True, verbose_name=_("Day"))

    class Meta:
        verbose_name        = _("Weekday")
        verbose_name_plural = _("Weekdays")
        ordering            = ["day"]

    def __str__(self):
        return self.get_day_display()

# =============================================================================
# Location
# =============================================================================
class Location(models.Model):
    created_at   = models.DateTimeField(auto_now_add=True)
    
    category     = models.ForeignKey(
        LocationCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="locations", 
        verbose_name=_("Category")
    )
    
    # Raje3na el partner hna bch el GraphQL yal9ah
    partner = models.ForeignKey(
        'partners.Partner', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="owned_locations", 
        verbose_name=_("Partner")
    )

    name         = models.CharField(max_length=255)
    country      = models.ForeignKey(
        "cities_light.Country", 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="locations", 
        verbose_name=_("Country")
    )
    city         = models.ForeignKey(
        "cities_light.City", 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="locations", 
        verbose_name=_("City")
    )
    
    longitude    = models.DecimalField(max_digits=9, decimal_places=6)
    latitude     = models.DecimalField(max_digits=9, decimal_places=6)
    is_active_ads = models.BooleanField(default=False, verbose_name=_("Active Ads"))
    story        = HTMLField(verbose_name=_("Story"))
    
    openFrom     = models.TimeField(
        verbose_name=_("Open From"), 
        blank=True, 
        null=True, 
        help_text=_("Add opening hours if the location is open from a specific time")
    )
    openTo       = models.TimeField(
        verbose_name=_("Open To"), 
        blank=True, 
        null=True, 
        help_text=_("Add opening hours if the location is open to a specific time")
    )
    admissionFee = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name=_("Admission Fee"), 
        blank=True, 
        null=True, 
        help_text=_("Add admission fee if the location has a specific admission fee")
    )
    closedDays   = models.ManyToManyField(
        "Weekday", 
        verbose_name=_("Closed Days"), 
        blank=True, 
        related_name="locations"
    )

    class Meta:
        verbose_name         = _("Location")
        verbose_name_plural  = _("Locations")

    def __str__(self):
        return self.name

# =============================================================================
# HIKING
# =============================================================================
class HikingLocation(models.Model):
    hiking   = models.ForeignKey("Hiking", on_delete=models.CASCADE)
    location = models.ForeignKey("Location", on_delete=models.CASCADE)
    order    = models.PositiveIntegerField(default=0)

    class Meta:
        ordering      = ["order"]
        unique_together = ["hiking", "location"]

    def __str__(self):
        return f"{self.hiking.name} - {self.location.name}"


class Hiking(models.Model):
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    city        = models.ForeignKey("cities_light.City", on_delete=models.SET_NULL, null=True, blank=True, related_name="hikings", verbose_name=_("Cities"))
    name        = models.CharField(_("Name"), max_length=255)
    description = models.TextField(_("Description"))
    locations   = models.ManyToManyField("Location", through="HikingLocation", verbose_name=_("Location"))
    latitude    = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude   = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        verbose_name        = _("Hiking")
        verbose_name_plural = _("Hikings")

    def __str__(self):
        return self.name


# =============================================================================
# EVENT
# =============================================================================
class EventCategory(models.Model):
    name       = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = _("Event Category")
        verbose_name_plural = _("Event Categories")

    def __str__(self):
        return self.name


class Event(models.Model):
    created_at      = models.DateTimeField(auto_now_add=True)
    client          = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="events", verbose_name=_("Client"))
    city            = models.ForeignKey("cities_light.City", on_delete=models.SET_NULL, null=True, blank=True, related_name="events", verbose_name=_("City"))
    category        = models.ForeignKey(EventCategory, on_delete=models.CASCADE, related_name="events", verbose_name=_("Category"))
    name            = models.CharField(max_length=255)
    location        = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name="events", verbose_name=_("Location"))
    startDate       = models.DateField(verbose_name=_("Start Date"))
    endDate         = models.DateField(verbose_name=_("End Date"))
    time            = models.TimeField(verbose_name=_("Time"))
    price           = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Price"))
    link            = models.URLField(verbose_name=_("The link to subscribe"))
    short_link      = models.URLField(blank=True, null=True)
    short_id        = models.CharField(max_length=50, blank=True, null=True)
    description     = HTMLField(verbose_name=_("Description"))
    boost           = models.BooleanField(default=False)
    is_paid         = models.BooleanField(default=False)
    clicks          = models.IntegerField(default=0)
    reminder_status = models.JSONField(default=list, blank=True)

    class Meta:
        verbose_name        = _("Event")
        verbose_name_plural = _("Events")

    def __str__(self):
        return self.name


# =============================================================================
# TIP
# =============================================================================
class Tip(models.Model):
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    city        = models.ForeignKey("cities_light.City", on_delete=models.SET_NULL, null=True, blank=True, related_name="tips", verbose_name=_("Cities"))
    description = HTMLField()

    class Meta:
        verbose_name        = _("Tip")
        verbose_name_plural = _("Tips")

    def __str__(self):
        return self.city.name


# =============================================================================
# AD
# =============================================================================
class Ad(models.Model):

    class Status(models.TextChoices):
        PENDING_PAYMENT = 'pending_payment', _('En attente de paiement')
        ACTIVE          = 'active',          _('Active')
        FINISHED        = 'finished',        _('Terminée')

    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)
    name            = models.CharField(max_length=255, verbose_name=_("Nom de la pub"), blank=True, null=True)
    country         = models.ForeignKey("cities_light.Country", on_delete=models.SET_NULL, null=True, blank=True, related_name="ads", verbose_name=_("Pays"))
    city            = models.ForeignKey("cities_light.City", on_delete=models.SET_NULL, null=True, blank=True, related_name="ads", verbose_name=_("Ville"))

    # ── CORRECTION : UserProfile vient de shared.models, pas de accounts ──
    client          = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="ads", verbose_name=_("Client"))

    image_mobile    = models.ImageField(upload_to="ads/mobile/", help_text=_("Taille : 320x50 pixels"), verbose_name=_("Image Mobile (320x50)"), null=True, blank=True)
    image_tablet    = models.ImageField(upload_to="ads/tablet/", help_text=_("Taille : 728x90 pixels"), verbose_name=_("Image Tablette (728x90)"), null=True, blank=True)
    link            = models.URLField(verbose_name=_("Lien"))
    short_link      = models.URLField(blank=True, null=True)
    short_id        = models.CharField(max_length=50, blank=True, null=True)
    clicks          = models.IntegerField(default=0)
    db_clicks_count = models.IntegerField(default=0)
    startDate       = models.DateField(null=True, blank=True, verbose_name=_("Date de début"))
    endDate         = models.DateField(null=True, blank=True, verbose_name=_("Date de fin"))
    total_price     = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_paid         = models.BooleanField(default=False, verbose_name=_("Payée"))
    is_active       = models.BooleanField(default=True, verbose_name=_("Active"))
    payment_ref     = models.CharField(max_length=100, blank=True, null=True)   # ← Konnect paymentRef

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING_PAYMENT,
        verbose_name=_("Statut"),
        db_index=True,
    )

    class Meta:
        verbose_name        = _("Pub")
        verbose_name_plural = _("Pubs")
        ordering            = ["-created_at"]

    def sync_status(self):
        from django.utils import timezone
        today = timezone.now().date()
        if not self.is_paid:
            self.status = self.Status.PENDING_PAYMENT
        elif self.endDate and today > self.endDate:
            self.status = self.Status.FINISHED
        else:
            self.status = self.Status.ACTIVE

    def save(self, *args, **kwargs):
        # 1. Nom auto si vide
        if not self.name:
            self.name = f"ADS-{uuid.uuid4().hex[:6].upper()}"

        # 2. Synchronise le statut
        self.sync_status()

        # 3. Optimise les images
        for field_name in ["image_mobile", "image_tablet"]:
            field = getattr(self, field_name)
            if field and hasattr(field, 'file') and isinstance(field.file, UploadedFile):
                try:
                    optimized = optimize_image(field)   # ← depuis shared.utils
                    if optimized:
                        _, content = optimized
                        content.name = f"{uuid.uuid4()}.jpg"
                        setattr(self, field_name, content)
                except Exception:
                    pass

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name or self.link


@receiver(post_delete, sender=Ad)
def cleanup_ad_images(sender, instance, **kwargs):
    for field_name in ["image_mobile", "image_tablet"]:
        field = getattr(instance, field_name)
        if field and field.name:
            try:
                if os.path.isfile(field.path):
                    os.remove(field.path)
            except Exception:
                pass


# =============================================================================
# PUBLIC TRANSPORT
# =============================================================================
class PublicTransportType(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name        = _("Public Transport Type")
        verbose_name_plural = _("Public Transport Types")

    def __str__(self):
        return self.name


class PublicTransport(models.Model):
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)
    publicTransportType = models.ForeignKey("PublicTransportType", on_delete=models.SET_NULL, null=True, blank=True, related_name="public_transports", verbose_name=_("Public Transport Type"))
    city                = models.ForeignKey("cities_light.City", on_delete=models.SET_NULL, null=True, blank=True, related_name="public_transports", verbose_name=_("City"))
    fromCity            = models.ForeignKey("cities_light.City", on_delete=models.SET_NULL, null=True, blank=True, related_name="from_city_trips", verbose_name=_("From City"))
    toCity              = models.ForeignKey("cities_light.City", on_delete=models.SET_NULL, null=True, blank=True, related_name="to_city_trips", verbose_name=_("To City"))
    fromRegion          = models.ForeignKey("cities_light.SubRegion", on_delete=models.SET_NULL, null=True, blank=True, related_name="from_region_trips", verbose_name=_("From Region"))
    toRegion            = models.ForeignKey("cities_light.SubRegion", on_delete=models.SET_NULL, null=True, blank=True, related_name="to_region_trips", verbose_name=_("To Region"))
    busNumber           = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("Line Number"))
    is_return_journey   = models.BooleanField(default=False, verbose_name=_("Is Return Journey"), help_text=_("Check this box if this is a return journey"))

    class Meta:
        verbose_name        = _("Public Transport")
        verbose_name_plural = _("Public Transports")

    def __str__(self):
        tp = self.publicTransportType.name.lower() if self.publicTransportType else ""
        if "train" in tp:
            return f"{self.publicTransportType} : {self.fromCity} → {self.toCity}"
        return f"{self.publicTransportType} ({self.busNumber}) - {self.city}"


class PublicTransportTime(models.Model):
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)
    publicTransport = models.ForeignKey("PublicTransport", on_delete=models.CASCADE, related_name="publicTransportTimes", verbose_name=_("Public Transport"))
    time            = models.TimeField(verbose_name=_("Departure Time"))
    returnTime      = models.TimeField(null=True, blank=True, verbose_name=_("Return Time"))

    class Meta:
        verbose_name        = _("Public Transport Time")
        verbose_name_plural = _("Public Transport Times")

    def __str__(self):
        return str(self.time)


# =============================================================================
# PARTNER & SPONSOR
# =============================================================================
class LegacyPartner(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    
    # --- AJOUT: Email indispensable pour envoyer le lien de validation ---
    email = models.EmailField(unique=True, verbose_name=_("Email"), null=True, blank=True)
    
    image = models.ImageField(upload_to="partners/", verbose_name=_("Image"))
    link = models.URLField(verbose_name=_("Link"))
    
    # --- MODIFICATION: Relation Many-to-Many pour assigner plusieurs localisations ---
    locations = models.ManyToManyField(
        "Location", 
        blank=True, 
        related_name="legacy_partners", 
        verbose_name=_("Locations")
    )
    
    # --- AJOUT: Pour savoir si le partenaire a validé son compte ---
    is_verified = models.BooleanField(default=False, verbose_name=_("Is Verified"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Partner")
        verbose_name_plural = _("Partners")

    def save(self, *args, **kwargs):
        # Ta logique existante de redimensionnement
        if self.image and hasattr(self.image, 'file') and isinstance(self.image.file, UploadedFile):
            processed = resize_to_fixed(self.image, size=(300, 200))
            if processed:
                name, content = processed
                content.name = name
                self.image = content
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Sponsor(models.Model):
    name  = models.CharField(max_length=255, verbose_name=_("Name"))
    image = models.ImageField(upload_to="sponsors/", verbose_name=_("Image"))
    link  = models.URLField(verbose_name=_("Link"))

    class Meta:
        verbose_name        = _("sponsor")
        verbose_name_plural = _("sponsors")

    def __str__(self):
        return self.name


@receiver(post_delete, sender=LegacyPartner)
@receiver(post_delete, sender=Sponsor)
def cleanup_all_files(sender, instance, **kwargs):
    for field in instance._meta.fields:
        if isinstance(field, FileField):
            file_field = getattr(instance, field.name)
            if file_field and file_field.name:
                try:
                    file_field.storage.delete(file_field.name)
                except Exception as e:
                    print(f"Error deleting file: {e}")


# =============================================================================
# CITY (nécessaire pour forms.py qui l'importe depuis guard.models)
# =============================================================================
class City(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# =============================================================================
# CLICKS
# =============================================================================
class AdClick(models.Model):
    ad         = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name="click_records")
    clicked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = _("Ad Click Record")
        verbose_name_plural = _("Ad Click Records")


class EventClick(models.Model):
    event      = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="click_records")
    clicked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = _("Event Click Record")
        verbose_name_plural = _("Event Click Records")


# =============================================================================
# SYSTEM LOGS & STATISTICS
# =============================================================================

class DashboardStatistics(models.Model):
    total_locations = models.IntegerField(default=0)
    locations_this_month = models.IntegerField(default=0)
    total_events = models.IntegerField(default=0)
    upcoming_events = models.IntegerField(default=0)
    events_this_month = models.IntegerField(default=0)
    total_hikings = models.IntegerField(default=0)
    hikings_this_month = models.IntegerField(default=0)
    total_ads = models.IntegerField(default=0)
    active_ads = models.IntegerField(default=0)
    total_fcm_devices = models.IntegerField(default=0)
    ios_devices = models.IntegerField(default=0)
    android_devices = models.IntegerField(default=0)
    active_users_30d = models.IntegerField(default=0)
    notifications_sent_24h = models.IntegerField(default=0)
    notifications_failed_24h = models.IntegerField(default=0)
    error_count_24h = models.IntegerField(default=0)
    last_error_message = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Dashboard Statistics")
        verbose_name_plural = _("Dashboard Statistics")

    def __str__(self):
        return f"Stats {self.updated_at.strftime('%Y-%m-%d %H:%M')}"


class ActivityLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    activity_type = models.CharField(max_length=100)
    entity_name = models.CharField(max_length=255)
    entity_type = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=255)
    user = models.CharField(max_length=255, blank=True, null=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("Activity Log")
        verbose_name_plural = _("Activity Logs")

    def __str__(self):
        return f"{self.activity_type} - {self.entity_name} ({self.timestamp})"


class NotificationLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    notification_type = models.CharField(max_length=100)
    status = models.CharField(max_length=50)
    device_count_attempted = models.IntegerField(default=0)
    device_count_succeeded = models.IntegerField(default=0)
    title = models.CharField(max_length=255)
    body = models.TextField()
    entity_type = models.CharField(max_length=100, blank=True, null=True)
    entity_id = models.CharField(max_length=255, blank=True, null=True)
    response = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("Notification Log")
        verbose_name_plural = _("Notification Logs")

    def __str__(self):
        return f"{self.notification_type} - {self.title} ({self.timestamp})"



class GuardUser(AbstractBaseUser, PermissionsMixin, UUIDModel, TimeStampedModel):
    # التغيير الأساسي: إضافة unique=True
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    objects = CustomUserManager()
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        # تصليح: نضمنوا إنها ترجع string ديما
        return self.username if self.username else self.email


class EmailVerificationToken(UUIDModel, TimeStampedModel):
    user = models.ForeignKey('GuardUser', on_delete=models.CASCADE, related_name='verification_tokens')
    token_hash = models.CharField(max_length=64, unique=True) # SHA-256 fait 64 caractères
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    @staticmethod
    def hash_token(raw_token):
        return hashlib.sha256(raw_token.encode()).hexdigest()

