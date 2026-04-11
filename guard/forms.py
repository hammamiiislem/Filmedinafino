from django import forms
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _
from tinymce.widgets import TinyMCE
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
 
from .models import Ad

from .models import (
    Location,
    ImageLocation,
    Event,
    City,
    ImageEvent,
    Tip,
    Hiking,
    HikingLocation,
    ImageHiking,
    Ad,
    ImageAd,
    PublicTransport,
    PublicTransportTime,
    Partner,
    Sponsor,
)

class FlowbiteFormMixin:
    input_class = (
        "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg "
        "focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 "
        "dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 "
        "dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
    )

    file_input_class = (
        "block w-full text-sm text-gray-900 border border-gray-300 rounded-lg "
        "cursor-pointer bg-gray-50 dark:text-gray-400 focus:outline-none "
        "dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400"
    )

    checkbox_class = "w-5 h-5 border border-default-medium rounded bg-neutral-secondary-medium focus:ring-2 focus:ring-brand-soft"
    radio_class = "w-4 h-4 text-blue-600 focus:ring-2 focus:ring-blue-500"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Mapping of widget types to their respective CSS classes
        widget_css_map = {
            forms.CheckboxInput: self.checkbox_class,
            forms.RadioSelect: self.radio_class,
            forms.FileInput: self.file_input_class,
        }

        for name, field in self.fields.items():
            widget = field.widget
            classes = widget.attrs.get("class", "")
            
            # Determine class based on mapping, defaulting to input_class
            base_class = next((cls for widget_type, cls in widget_css_map.items() 
                              if isinstance(widget, widget_type)), self.input_class)
            
            widget.attrs["class"] = f"{classes} {base_class}".strip()
            widget.attrs.setdefault("id", f"id_{name}")

class LocationForm(FlowbiteFormMixin, forms.ModelForm):
    name_en = forms.CharField(
        label=_("Name (English)"),
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": _("Enter location name in English")}),
        error_messages={"required": _("Please enter the name in English.")},
    )
    name_fr = forms.CharField(
        label=_("Name (French)"),
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": _("Enter location name in French")}),
        error_messages={"required": _("Please enter the name in French.")},
    )

    story_en = forms.CharField(
        label=_("Story (English)"),
        required=True,
        widget=TinyMCE(attrs={"cols": 80, "rows": 30}),
        error_messages={"required": _("Please enter the story in English.")},
    )
    story_fr = forms.CharField(
        label=_("Story (French)"),
        required=True,
        widget=TinyMCE(attrs={"cols": 80, "rows": 30}),
        error_messages={"required": _("Please enter the story in French.")},
    )

    class Meta:
        model = Location
        fields = [
            "name_en", "name_fr", "category", "country", "city", 
            "latitude", "longitude", "story_en", "story_fr", 
            "openFrom", "openTo", "admissionFee", "is_active_ads", "closedDays",
        ]
        widgets = {
            "category": forms.Select(attrs={"placeholder": _("Select location category"), "required": True}),
            "country": forms.Select(attrs={"placeholder": _("Select location country"), "required": True}),
            "city": forms.Select(attrs={"placeholder": _("Select location city"), "required": True}),
            "latitude": forms.NumberInput(attrs={"placeholder": _("e.g., 36.8065"), "step": "0.000001"}),
            "longitude": forms.NumberInput(attrs={"placeholder": _("e.g., 10.1815"), "step": "0.000001"}),
            "openFrom": forms.TimeInput(attrs={"type": "time", "placeholder": _("Opening time")}),
            "openTo": forms.TimeInput(attrs={"type": "time", "placeholder": _("Closing time")}),
            "admissionFee": forms.NumberInput(attrs={"placeholder": _("e.g., 5.00"), "step": "0.01", "min": "0"}),
            "is_active_ads": forms.CheckboxInput(),
            "closedDays": forms.CheckboxSelectMultiple(attrs={"class": "w-5 h-5 border border-default-medium rounded bg-neutral-secondary-medium focus:ring-2 focus:ring-brand-soft"}),
        }

        error_messages = {
            "category": {"required": _("Please select a category.")},
            "country": {"required": _("Please select a country.")},
            "city": {"required": _("Please select a city.")},
        }

        help_texts = {
            "latitude": _("Latitude in decimal degrees (e.g., 36.8065)"),
            "longitude": _("Longitude in decimal degrees (e.g., 10.1815)"),
            "openFrom": _("Leave empty if location is always open"),
            "openTo": _("Leave empty if location is always open"),
            "admissionFee": _("Leave empty if admission is free"),
            "is_active_ads": _("Enable advertisements for this location"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ["category", "country", "city"]:
            if field_name in self.fields:
                self.fields[field_name].required = True

        if "city" in self.fields:
            from cities_light.models import City
            qs = City.objects.filter(country=self.instance.country) if self.instance and self.instance.country else City.objects.all()
            self.fields["city"].queryset = qs

    def clean(self):
        cleaned_data = super().clean()
        
        multilingual_reqs = {
            "name_en": _("Please enter the name in English."),
            "name_fr": _("Please enter the name in French."),
            "story_en": _("Please enter the story in English."),
            "story_fr": _("Please enter the story in French."),
        }

        for field, message in multilingual_reqs.items():
            if not cleaned_data.get(field):
                self.add_error(None, message)
                self.errors.pop(field, None)

        open_from, open_to = cleaned_data.get("openFrom"), cleaned_data.get("openTo")
        if open_from and open_to and open_from >= open_to:
            self.add_error("openTo", _("Opening time must be before closing time."))

        return cleaned_data

class ImageLocationForm(forms.ModelForm):
    class Meta:
        model = ImageLocation
        fields = ["image"]
        widgets = {
            "image": forms.FileInput(attrs={
                "class": "block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 dark:text-gray-400 focus:outline-none dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400",
                "accept": "image/*",
            })
        }

ImageLocationFormSet = inlineformset_factory(
    Location, ImageLocation, form=ImageLocationForm, extra=1, can_delete=True, max_num=10,
)

class EventForm(FlowbiteFormMixin, forms.ModelForm):
    name_en = forms.CharField(
        label=_("Name (English)"), max_length=255, required=True,
        widget=forms.TextInput(attrs={"placeholder": _("Enter event name in English")}),
        error_messages={"required": _("Please enter the name in English.")},
    )
    name_fr = forms.CharField(
        label=_("Name (French)"), max_length=255, required=True,
        widget=forms.TextInput(attrs={"placeholder": _("Enter event name in French")}),
        error_messages={"required": _("Please enter the name in French.")},
    )
    description_en = forms.CharField(
        label=_("Description (English)"), required=True,
        widget=TinyMCE(attrs={"cols": 80, "rows": 30}),
        error_messages={"required": _("Please enter the description in English.")},
    )
    description_fr = forms.CharField(
        label=_("Description (French)"), required=True,
        widget=TinyMCE(attrs={"cols": 80, "rows": 30}),
        error_messages={"required": _("Please enter the description in French.")},
    )
    link = forms.URLField(
        label=_("Destination Link"), required=True,
        widget=forms.URLInput(attrs={"placeholder": "https://example.com"}),
        help_text=_("The destination URL for this event."),
    )

    country = forms.ModelChoiceField(
        queryset=None,
        label=_("Country"),
        required=False,
        widget=forms.Select(attrs={"placeholder": _("Select country")}),
    )

    class Meta:
        model = Event
        fields = ["name_en", "name_fr", "description_en", "description_fr", "country", "city", "location", "category", "startDate", "endDate", "time", "price", "link", "boost"]
        widgets = {
            "location": forms.Select(attrs={"placeholder": _("Select event location")}),
            "city": forms.Select(attrs={"placeholder": _("Select city")}),
            "category": forms.Select(attrs={"placeholder": _("Select event category")}),
            "startDate": forms.DateInput(attrs={"type": "date", "placeholder": _("Select event start date")}),
            "endDate": forms.DateInput(attrs={"type": "date", "placeholder": _("Select event end date")}),
            "time": forms.TimeInput(attrs={"type": "time", "placeholder": _("Select event time")}),
            "price": forms.NumberInput(attrs={"placeholder": _("Enter event price"), "step": "0.01", "min": "0"}),
            "link": forms.URLInput(attrs={"placeholder": "https://example.com"}),
            "boost": forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        from cities_light.models import Country, City

        self.fields["country"].queryset = Country.objects.all()

        if "city" in self.fields:
            self.fields["city"].required = True
            
            # Handle filtered querysets based on selected country/city (instance or POST data)
            country_id = None
            city_id = None
            
            if self.data.get("country"):
                country_id = self.data.get("country")
            elif self.instance.pk and self.instance.city:
                country_id = self.instance.city.country_id
                self.fields["country"].initial = self.instance.city.country
            
            if country_id:
                self.fields["city"].queryset = City.objects.filter(country_id=country_id)
            else:
                self.fields["city"].queryset = City.objects.all()

            if self.data.get("city"):
                city_id = self.data.get("city")
            elif self.instance.pk and self.instance.city:
                city_id = self.instance.city_id
            
            if city_id:
                self.fields["location"].queryset = Location.objects.filter(city_id=city_id)
            else:
                self.fields["location"].queryset = Location.objects.all()

        if user and not (user.is_staff or user.is_superuser):
            self.fields.pop("boost", None)

    def clean_startDate(self):
        start_date = self.cleaned_data.get("startDate")
        if start_date:
            from django.utils import timezone
            from datetime import timedelta
            min_date = timezone.now().date() + timedelta(days=14)
            if start_date < min_date:
                raise forms.ValidationError(
                    _("Events must be published at least 2 weeks before the event date. Earliest allowed: %(date)s") % {"date": min_date}
                )
        return start_date

    def clean(self):
        cleaned_data = super().clean()
        fields_to_check = {
            "name_en": _("Please enter the name in English."),
            "name_fr": _("Please enter the name in French."),
            "description_en": _("Please enter the description in English."),
            "description_fr": _("Please enter the description in French."),
        }
        for field, msg in fields_to_check.items():
            if not cleaned_data.get(field):
                self.add_error(None, msg)
                self.errors.pop(field, None)
        
        start_date = cleaned_data.get("startDate")
        end_date = cleaned_data.get("endDate")
        if start_date and end_date and start_date > end_date:
            self.add_error("endDate", _("End date must be after start date."))

        return cleaned_data

class ImageEventForm(forms.ModelForm):
    class Meta:
        model = ImageEvent
        fields = ["image"]
        widgets = {
            "image": forms.FileInput(attrs={
                "class": "block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 dark:text-gray-400 focus:outline-none dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400",
                "accept": "image/*",
            })
        }

ImageEventFormSet = inlineformset_factory(
    Event, ImageEvent, form=ImageEventForm, extra=1, can_delete=True, max_num=10,
)

class TipForm(FlowbiteFormMixin, forms.ModelForm):
    description_en = forms.CharField(label=_("Description (English)"), required=True, widget=TinyMCE(attrs={"cols": 80, "rows": 30}))
    description_fr = forms.CharField(label=_("Description (French)"), required=True, widget=TinyMCE(attrs={"cols": 80, "rows": 30}))

    class Meta:
        model = Tip
        fields = ["city", "description_en", "description_fr"]
        widgets = {"city": forms.Select(attrs={"placeholder": _("Select city"), "required": True})}
        error_messages = {"city": {"required": _("Please select a city.")}}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "city" in self.fields:
            self.fields["city"].required = True

    def clean(self):
        cleaned_data = super().clean()
        required_fields = {
            "description_en": _("Description (English) is required."),
            "description_fr": _("Description (French) is required."),
        }
        for field, error in required_fields.items():
            if not cleaned_data.get(field):
                self.add_error(None, error)
                self._errors.pop(field, None)
        return cleaned_data

class HikingForm(FlowbiteFormMixin, forms.ModelForm):
    name_en = forms.CharField(label=_("Name (English)"), required=True, error_messages={"required": _("Please enter the name in English.")})
    name_fr = forms.CharField(label=_("Name (French)"), required=True, error_messages={"required": _("Please enter the name in French.")})
    description_en = forms.CharField(label=_("Description (English)"), required=True, widget=TinyMCE(attrs={"cols": 80, "rows": 30}), error_messages={"required": _("Please enter the description in English.")})
    description_fr = forms.CharField(label=_("Description (French)"), required=True, widget=TinyMCE(attrs={"cols": 80, "rows": 30}), error_messages={"required": _("Please enter the description in French.")})

    class Meta:
        model = Hiking
        fields = ["name_en", "name_fr", "description_en", "description_fr", "city", "latitude", "longitude"]
        widgets = {
            "city": forms.Select(attrs={"placeholder": _("Select city"), "class": "block w-full px-3 py-2.5 bg-neutral-secondary-medium border border-default-medium text-heading text-sm rounded-base focus:ring-brand focus:border-brand shadow-xs placeholder:text-body", "required": True}),
            "latitude": forms.NumberInput(attrs={"placeholder": _("e.g., 36.8065"), "step": "0.000001"}),
            "longitude": forms.NumberInput(attrs={"placeholder": _("e.g., 10.1815"), "step": "0.000001"}),
        }
        error_messages = {"city": {"required": _("Please select a city.")}}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "city" in self.fields:
            self.fields["city"].required = True

    def clean(self):
        cleaned_data = super().clean()
        check_fields = {
            "name_en": _("Please enter the name in English."),
            "name_fr": _("Please enter the name in French."),
            "description_en": _("Please enter the description in English."),
            "description_fr": _("Please enter the description in French."),
        }
        for field, msg in check_fields.items():
            if not cleaned_data.get(field):
                self.add_error(None, msg)
                self.errors.pop(field, None)
        return cleaned_data

class HikingLocationForm(FlowbiteFormMixin, forms.ModelForm):
    class Meta:
        model = HikingLocation
        fields = ["location", "order"]
        widgets = {
            "location": forms.Select(attrs={"class": "block w-full px-3 py-2.5 bg-neutral-secondary-medium border border-default-medium text-heading text-sm rounded-base focus:ring-brand focus:border-brand shadow-xs placeholder:text-body", "placeholder": _("Select location")}),
            "order": forms.HiddenInput(),
        }

HikingLocationFormSet = inlineformset_factory(
    Hiking, HikingLocation, form=HikingLocationForm, extra=1, can_delete=True, fields=["location", "order"],
)

class ImageHikingForm(forms.ModelForm):
    class Meta:
        model = ImageHiking
        fields = ["image"]
        widgets = {
            "image": forms.FileInput(attrs={
                "class": "block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 dark:text-gray-400 focus:outline-none dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400",
                "accept": "image/*",
            })
        }

ImageHikingFormSet = inlineformset_factory(
    Hiking, ImageHiking, form=ImageHikingForm, extra=1, can_delete=True, max_num=10,
)

class AdForm(forms.ModelForm):
 
    DAILY_AD_RATE = Decimal('5.00')   # 5$ par jour — change ici si besoin
 
    name = forms.CharField(
        label=_("Nom de la pub"),
        required=False,
        widget=forms.TextInput(attrs={
            "placeholder": _("ex : Campagne Été 2026"),
            "class": "block w-full rounded-lg border border-gray-300 bg-gray-50 p-2.5 text-sm text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:border-blue-500 dark:focus:ring-blue-500",
        }),
        help_text=_("Laissez vide pour générer automatiquement un nom type 'ADS-XXXXXX'."),
    )
 
    startDate = forms.DateField(
        label=_("Date de début"),
        widget=forms.DateInput(attrs={
            "type": "date",
            "class": "block w-full rounded-lg border border-gray-300 bg-gray-50 p-2.5 text-sm text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:border-blue-500 dark:focus:ring-blue-500",
        }),
    )
 
    endDate = forms.DateField(
        label=_("Date de fin"),
        widget=forms.DateInput(attrs={
            "type": "date",
            "class": "block w-full rounded-lg border border-gray-300 bg-gray-50 p-2.5 text-sm text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:border-blue-500 dark:focus:ring-blue-500",
        }),
    )
 
    class Meta:
        model  = Ad
        fields = [
            "name", "country", "city",
            "startDate", "endDate",
            "image_mobile", "image_tablet",
            "link", "is_active",
        ]
        widgets = {
            "country": forms.Select(attrs={
                "class": "block w-full rounded-lg border border-gray-300 bg-gray-50 p-2.5 text-sm text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:border-blue-500 dark:focus:ring-blue-500",
            }),
            "city": forms.Select(attrs={
                "class": "block w-full rounded-lg border border-gray-300 bg-gray-50 p-2.5 text-sm text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:border-blue-500 dark:focus:ring-blue-500",
            }),
            "link": forms.URLInput(attrs={
                "placeholder": "https://exemple.com",
                "class": "block w-full rounded-lg border border-gray-300 bg-gray-50 p-2.5 text-sm text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:border-blue-500 dark:focus:ring-blue-500",
            }),
            "image_mobile": forms.FileInput(attrs={
                "accept": "image/*",
                "class": "block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 dark:text-gray-400 focus:outline-none dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400",
            }),
            "image_tablet": forms.FileInput(attrs={
                "accept": "image/*",
                "class": "block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 dark:text-gray-400 focus:outline-none dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400",
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600",
            }),
        }
 
    # ─────────────────────────────────────────────────────────────────────────
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
 
        # Date minimum = demain
        tomorrow = (timezone.now().date() + timedelta(days=1)).isoformat()
        self.fields["startDate"].widget.attrs["min"] = tomorrow
 
        # Champs obligatoires
        self.fields["country"].required = True
        self.fields["city"].required    = False
        self.fields["link"].required    = True
 
        # Images obligatoires seulement à la création
        is_new = not (self.instance and self.instance.pk)
        self.fields["image_mobile"].required = is_new
        self.fields["image_tablet"].required = is_new
 
    # ─────────────────────────────────────────────────────────────────────────
    # Validation de la date de début
    # ─────────────────────────────────────────────────────────────────────────
    def clean_startDate(self):
        start_date = self.cleaned_data.get("startDate")
        if start_date:
            if start_date <= timezone.now().date():
                raise forms.ValidationError(
                    _("La date de début doit être au minimum demain.")
                )
        return start_date
 
    # ─────────────────────────────────────────────────────────────────────────
    # Validation croisée dates + calcul du prix côté serveur
    # ─────────────────────────────────────────────────────────────────────────
    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("startDate")
        end   = cleaned_data.get("endDate")
 
        if start and end:
            if end <= start:
                self.add_error(
                    "endDate",
                    _("La date de fin doit être après la date de début.")
                )
            else:
                days = (end - start).days
                cleaned_data['total_price'] = Decimal(str(days)) * self.DAILY_AD_RATE
                cleaned_data['days']        = days
 
        return cleaned_data
 
    # ─────────────────────────────────────────────────────────────────────────
    # Validation des dimensions des images
    # ─────────────────────────────────────────────────────────────────────────
    def _get_dimensions(self, image):
        if hasattr(image, "image"):
            return image.image.width, image.image.height
        from django.core.files.images import get_image_dimensions
        return get_image_dimensions(image)
 
    def clean_image_mobile(self):
        image = self.cleaned_data.get("image_mobile")
        if image and hasattr(image, 'size'):   # c'est un nouveau fichier uploadé
            w, h = self._get_dimensions(image)
            if w != 320 or h != 50:
                raise forms.ValidationError(
                    _("L'image mobile doit faire exactement 320x50 pixels. Reçu : %(w)sx%(h)s")
                    % {"w": w, "h": h}
                )
        return image
 
    def clean_image_tablet(self):
        image = self.cleaned_data.get("image_tablet")
        if image and hasattr(image, 'size'):
            w, h = self._get_dimensions(image)
            if w != 728 or h != 90:
                raise forms.ValidationError(
                    _("L'image tablette doit faire exactement 728x90 pixels. Reçu : %(w)sx%(h)s")
                    % {"w": w, "h": h}
                )
        return image

class PartnerForm(FlowbiteFormMixin, forms.ModelForm):
    # Changement en ModelMultipleChoiceField pour gérer plusieurs sélections
    locations = forms.ModelMultipleChoiceField(
        queryset=Location.objects.all(),
        required=False,
        label=_("Assigned Locations"),
        # Utilisation de CheckboxSelectMultiple
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'space-y-2'
        }),
        help_text=_("Sélectionnez les emplacements associés à ce partenaire.")
    )

    class Meta:
        model = Partner
        fields = ["name", "email", "link", "image", "locations"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": _("Partner name")}),
            "email": forms.EmailInput(attrs={"placeholder": _("Partner email (for validation)")}),
            "link": forms.URLInput(attrs={"placeholder": _("Website or Social link")}),
            "image": forms.FileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # En mode "Edit", on pré-coche toutes les locations déjà liées
        if self.instance.pk:
            self.fields['locations'].initial = self.instance.locations.all()
class SponsorForm(FlowbiteFormMixin, forms.ModelForm):
    class Meta:
        model = Sponsor
        fields = ["name", "image", "link"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": _("e.g., Sponsor name")}),
            "link": forms.URLInput(attrs={"placeholder": "https://example.com"}),
            "image": forms.FileInput(attrs={"accept": "image/*"}),
        }
        error_messages = {
            "name": {"required": _("Please enter a name.")},
            "image": {"required": _("Please upload an image (300x200).")},
            "link": {"required": _("Please provide a link.")},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "image" in self.fields:
            self.fields["image"].required = not (self.instance and self.instance.pk)

class PublicTransportForm(FlowbiteFormMixin, forms.ModelForm):
    class Meta:
        model = PublicTransport
        fields = ("publicTransportType", "city", "fromCity", "toCity", "fromRegion", "toRegion", "busNumber", "is_return_journey")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False
        self.fields["publicTransportType"].required = True

        from cities_light.models import City as CitiesLightCity, SubRegion as CitiesLightSubRegion
        self.fields["fromCity"].queryset = self.fields["toCity"].queryset = CitiesLightCity.objects.all()
        self.fields["fromRegion"].queryset = self.fields["toRegion"].queryset = CitiesLightSubRegion.objects.all().order_by("name")

        type_id = self.data.get("publicTransportType") or (self.instance.publicTransportType.id if self.instance.pk and self.instance.publicTransportType else None)
        if type_id:
            from .models import PublicTransportType
            try:
                tp = PublicTransportType.objects.get(pk=type_id)
                name = tp.name.lower()
                
                # Logic Mapping for requirements
                if "bus" in name:
                    for f in ["city", "fromRegion", "toRegion", "busNumber"]: self.fields[f].required = True
                elif "train" in name:
                    for f in ["fromCity", "toCity"]: self.fields[f].required = True
            except PublicTransportType.DoesNotExist:
                pass

    def clean(self):
        cleaned_data = super().clean()
        type_id = self.data.get("publicTransportType") or (self.instance.publicTransportType.id if self.instance.pk and self.instance.publicTransportType else None)
        if type_id:
            from .models import PublicTransportType
            try:
                tp = PublicTransportType.objects.get(pk=type_id)
                if "metro" in tp.name.lower():
                    if not any([cleaned_data.get(f) for f in ["fromCity", "toCity", "fromRegion", "toRegion"]]):
                        raise forms.ValidationError(_("Pour Metro, veuillez renseigner soit City to City, soit Region to Region."))
            except PublicTransportType.DoesNotExist:
                pass
        return cleaned_data

class PublicTransportTimeForm(FlowbiteFormMixin, forms.ModelForm):
    class Meta:
        model = PublicTransportTime
        fields = ["time", "returnTime"]
        widgets = {
            "time": forms.TimeInput(attrs={"type": "time", "placeholder": _("Departure time")}),
            "returnTime": forms.TimeInput(attrs={"type": "time", "placeholder": _("Return time")}),
        }

PublicTransportFormSet = inlineformset_factory(
    PublicTransport, PublicTransportTime, form=PublicTransportTimeForm, extra=1, can_delete=True,
)