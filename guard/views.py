import datetime
import logging
import requests
import uuid

from decimal import Decimal
from shared.utils import send_validation_email

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.cache import cache
from django.db.models import Count, Sum, F
from django.db.models.functions import TruncDay
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import (
    CreateView, UpdateView, DeleteView,
    ListView, TemplateView, DetailView,
)

from .forms import (
    LocationForm, ImageLocationFormSet,
    EventForm, ImageEventFormSet,
    TipForm,
    HikingForm, HikingLocationFormSet, ImageHikingFormSet,
    AdForm,
    PublicTransportForm, PublicTransportFormSet,
    PartnerForm, SponsorForm,
)
from .models import (
    LocationCategory, Location,
    Event, EventCategory,
    UserProfile, Tip, Hiking,
    Ad,
    PublicTransport, PublicTransportType,
    Partner, Sponsor,
    AdClick, EventClick,
)
from events.models import Event as NewEvent

from datetime import timedelta
from shared.short_io import ShortIOService
from django.core import signing
from django.http import HttpResponse
from guard.models import Partner

logger = logging.getLogger(__name__)


# =============================================================================
# KONNECT — SERVICE
# =============================================================================
class KonnectService:
    BASE_URL = "https://api.konnect.network/api/v2"

    def __init__(self):
        self.api_key     = getattr(settings, 'KONNECT_API_KEY', '')
        self.receiver_id = getattr(settings, 'KONNECT_RECEIVER_WALLET_ID', '')
        self.headers     = {
            "x-api-key":    self.api_key,
            "Content-Type": "application/json",
        }

    def create_payment(self, amount_millimes, description, order_id, success_url, fail_url):
        # ── MOCK MODE for Testing ──
        return {
            "payment_url": success_url,
            "paymentRef": f"MOCK-{order_id}-{uuid.uuid4().hex[:6]}"
        }

    def get_payment_status(self, payment_ref):
        try:
            resp = requests.get(
                f"{self.BASE_URL}/payments/{payment_ref}",
                headers=self.headers,
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json().get("payment", {}).get("status")
        except requests.exceptions.RequestException as e:
            logger.error(f"Konnect get_payment_status error: {e}")
            return None


# =============================================================================
# DASHBOARD
# =============================================================================
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "guard/views/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_staff:
            context["admin_stats"] = {
                "locations":        Location.objects.count(),
                "events":           NewEvent.objects.count(),
                "hikings":          Hiking.objects.count(),
                "subscribers":      UserProfile.objects.filter(user_type=UserProfile.UserType.CLIENT_PARTNER).count(),
                "transports":       PublicTransport.objects.count(),
                "partners":         Partner.objects.count(),
                "sponsors":         Sponsor.objects.count(),
                "tips":             Tip.objects.count(),
                "event_categories": EventCategory.objects.count(),
            }
        else:
            profile = getattr(self.request.user, 'profile', None)
            if profile:
                context["last_event"] = NewEvent.objects.filter(partner=self.request.user).order_by('-created_at').first()
                context["last_ad"]    = Ad.objects.filter(client=profile).order_by('-created_at').first()
                
                # Stats for the 3 cards in the image
                context["card_stats"] = {
                    "events_count": NewEvent.objects.filter(partner=self.request.user).count(),
                    "ads_count": Ad.objects.filter(client=profile).count(),
                }

                # SaaS Alerts logic
                days_left = profile.subscription_days_left
                context["subscription_alerts"] = {
                    "is_unpaid": days_left is not None and days_left < 0,
                    "unpaid_days": abs(days_left) if days_left is not None and days_left < 0 else 0,
                    "is_expiring": profile.is_subscription_expiring,
                    "days_left": days_left,
                    "status_label": profile.subscription_status_label,
                    "renews_at": profile.subscription_renews_at,
                    "is_active": profile.subscription_status == 'active' or profile.subscription_status == 'trial',
                }
        return context


class DashboardStatsAPIView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        cache_key = f"dashboard_combined_stats_{'global' if request.user.is_staff else request.user.id}"
        stats = cache.get(cache_key)

        if not stats:
            end_date   = timezone.now()
            start_date = end_date - timedelta(days=6)

            def get_local_stats(model_class, ad_or_event_filter):
                clicks = model_class.objects.filter(
                    clicked_at__gte=start_date.replace(hour=0, minute=0, second=0, microsecond=0),
                    clicked_at__lte=end_date,  # ← ADD THIS
                    **ad_or_event_filter
                ).annotate(day=TruncDay('clicked_at')).values('day').annotate(count=Count('id')).order_by('day')    

                click_map = {}
                for c in clicks:
                    d = c['day']
                    if isinstance(d, str):
                        try:
                            d = datetime.datetime.strptime(d.split(' ')[0], '%Y-%m-%d').date()
                        except ValueError:
                            continue
                    elif hasattr(d, 'date'):
                        d = d.date()
                    click_map[d] = c['count']
                return click_map

            service = ShortIOService()
            if request.user.is_staff:
                ad_ids           = list(Ad.objects.filter(short_id__isnull=False).values_list("short_id", flat=True))
                event_ids        = list(Event.objects.filter(short_id__isnull=False).values_list("short_id", flat=True))
                local_ads_map    = get_local_stats(AdClick, {})
                local_events_map = get_local_stats(EventClick, {})
            else:
                profile = getattr(request.user, 'profile', None)
                if profile:
                    ad_ids           = list(Ad.objects.filter(client=profile, short_id__isnull=False).values_list("short_id", flat=True))
                    event_ids        = list(Event.objects.filter(client=profile, short_id__isnull=False).values_list("short_id", flat=True))
                    local_ads_map    = get_local_stats(AdClick, {"ad__client": profile})
                    local_events_map = get_local_stats(EventClick, {"event__client": profile})
                else:
                    ad_ids, event_ids = [], []
                    local_ads_map, local_events_map = {}, {}

            short_ads_stats    = service.get_aggregated_link_statistics(ad_ids, "week")
            short_events_stats = service.get_aggregated_link_statistics(event_ids, "week")

            def merge_stats(short_stats, local_map):
                timeline_map = {}
                for point in short_stats.get("clickStatistics", {}).get("timeline", []):
                    try:
                        m = point.get("moment")
                        if isinstance(m, str):
                            m = datetime.datetime.strptime(m.split('T')[0], '%Y-%m-%d').date()
                        elif hasattr(m, 'date'):
                            m = m.date()
                        if m:
                            timeline_map[m] = point.get("clicks", 0)
                    except (ValueError, TypeError, IndexError):
                        continue
                for day, count in local_map.items():
                    timeline_map[day] = timeline_map.get(day, 0) + count
                final_timeline = []
                for i in range(7):
                    day = (start_date + timedelta(days=i)).date()
                    final_timeline.append({"moment": day.isoformat(), "clicks": timeline_map.get(day, 0)})
                return {"totalClicks": sum(p['clicks'] for p in final_timeline), "clickStatistics": {"timeline": final_timeline}}

            stats = {
                "ads":    merge_stats(short_ads_stats,    local_ads_map),
                "events": merge_stats(short_events_stats, local_events_map),
            }
            cache.set(cache_key, stats, 30)

        return JsonResponse(stats)


def record_ad_click(request, ad_id):
    ad = get_object_or_404(Ad, pk=ad_id)
    AdClick.objects.create(ad=ad)
    # Remove the redundant db_clicks_count increment entirely
    # Invalidate both staff and user caches
    cache.delete("dashboard_combined_stats_global")
    if ad.client_id:
        cache.delete(f"dashboard_combined_stats_{ad.client.user_id}")
    return JsonResponse({"success": True})
 
 
def record_event_click(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    EventClick.objects.create(event=event)
    # ← CORRECTION : incrémente clicks sur Event
    Event.objects.filter(pk=event_id).update(clicks=F('clicks') + 1)
    return JsonResponse({"success": True})


# =============================================================================
# LOCATIONS
# =============================================================================
class LocationsListView(UserPassesTestMixin, LoginRequiredMixin, ListView):
    model = Location
    template_name = "guard/views/locations/list.html"
    context_object_name = "locations"
    ordering = ["-created_at"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["location_categories"] = LocationCategory.objects.all()
        return context

    def test_func(self):
        return self.request.user.is_staff


class LocationCreateView(UserPassesTestMixin, LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Location
    template_name = "guard/views/locations/index.html"
    form_class = LocationForm
    success_url = reverse_lazy("guard:locationsList")
    success_message = _("Location created successfully.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["image_formset"] = ImageLocationFormSet(self.request.POST, self.request.FILES) if self.request.POST else ImageLocationFormSet()
        return context

    def form_valid(self, form):
        print("--- DEBUG: DEBUT FORM_VALID ---")
        self.object = form.save()
    
        locations = form.cleaned_data.get('locations')
        if locations:
            print(f"--- DEBUG: LOCATIONS TROUVEES: {locations} ---")
        self.object.locations.set(locations)

        print("--- DEBUG: TENTATIVE ENVOI MAIL ---")
        try:
            from shared.utils import send_validation_email
            send_validation_email(self.object)
            print("--- DEBUG: FONCTION ENVOI EXÉCUTÉE ---")
        except Exception as e:
            print(f"--- DEBUG: ERREUR DANS VIEWS: {e} ---")

        return super().form_valid(form)
    def test_func(self):
        return self.request.user.is_staff


class LocationUpdateView(UserPassesTestMixin, LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Location
    template_name = "guard/views/locations/index.html"
    form_class = LocationForm
    success_url = reverse_lazy("guard:locationsList")
    success_message = _("Location updated successfully.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["image_formset"] = ImageLocationFormSet(self.request.POST, self.request.FILES, instance=self.object) if self.request.POST else ImageLocationFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        image_formset = context["image_formset"]
        if image_formset.is_valid():
            existing = sum(1 for f in image_formset if f.instance.pk and not f.cleaned_data.get("DELETE", False))
            new      = sum(1 for f in image_formset if f.cleaned_data.get("image") and not f.instance.pk)
            if existing + new < 1:
                form.add_error(None, _("Veuillez conserver ou télécharger au moins une image."))
                return self.form_invalid(form)
            self.object = form.save()
            image_formset.instance = self.object
            image_formset.save()
            return super().form_valid(form)
        return self.form_invalid(form)

    def test_func(self):
        return self.request.user.is_staff


class LocationDeleteView(UserPassesTestMixin, LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Location
    success_url = reverse_lazy("guard:locationsList")
    success_message = _("Unfortunately, this location has been deleted")

    def delete(self, request, *args, **kwargs):
        messages.warning(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)

    def test_func(self):
        return self.request.user.is_staff


# =============================================================================
# SUBSCRIBERS
# =============================================================================
class SubscribersListView(UserPassesTestMixin, LoginRequiredMixin, ListView):
    model = UserProfile
    template_name = "guard/views/subscribers/list.html"
    context_object_name = "subscribers"
    ordering = ["-created_at"]

    def get_queryset(self):
        return UserProfile.objects.filter(user_type=UserProfile.UserType.CLIENT_PARTNER)

    def test_func(self):
        return self.request.user.is_staff


# =============================================================================
# PUBLIC TRANSPORTS
# =============================================================================
def _apply_transport_type_logic(form, request, obj=None):
    from cities_light.models import City, SubRegion
    type_id = request.POST.get("publicTransportType") or (obj.publicTransportType.id if obj and obj.publicTransportType else None)
    transport_type_name = ""
    if type_id:
        try:
            tp = PublicTransportType.objects.get(pk=type_id)
            transport_type_name = tp.name.lower()
        except PublicTransportType.DoesNotExist:
            pass
    if not type_id:
        form.fields["fromCity"].queryset = City.objects.all()
        form.fields["toCity"].queryset   = City.objects.all()
    elif "train" in transport_type_name:
        form.fields["fromCity"].queryset   = City.objects.all()
        form.fields["toCity"].queryset     = City.objects.all()
        form.fields["fromRegion"].queryset = SubRegion.objects.none()
        form.fields["toRegion"].queryset   = SubRegion.objects.none()
    elif "metro" in transport_type_name:
        form.fields["fromCity"].queryset   = City.objects.all()
        form.fields["toCity"].queryset     = City.objects.all()
        form.fields["fromRegion"].queryset = SubRegion.objects.all().order_by("name")
        form.fields["toRegion"].queryset   = SubRegion.objects.all().order_by("name")
    else:
        city_id = request.POST.get("city") or (obj.city.id if obj and obj.city else None)
        if city_id:
            try:
                selected_city = City.objects.get(pk=city_id)
                form.fields["fromRegion"].queryset = SubRegion.objects.filter(region=selected_city.region)
                form.fields["toRegion"].queryset   = SubRegion.objects.filter(region=selected_city.region)
            except City.DoesNotExist:
                form.fields["fromRegion"].queryset = SubRegion.objects.none()
                form.fields["toRegion"].queryset   = SubRegion.objects.none()
        else:
            form.fields["fromRegion"].queryset = SubRegion.objects.none()
            form.fields["toRegion"].queryset   = SubRegion.objects.none()
        form.fields["fromCity"].queryset = City.objects.none()
        form.fields["toCity"].queryset   = City.objects.none()
    return form


class PublicTransportListView(UserPassesTestMixin, LoginRequiredMixin, ListView):
    model = PublicTransport
    template_name = "guard/views/publicTransports/list.html"
    context_object_name = "transports"
    ordering = ["-created_at"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["transport_types"] = PublicTransportType.objects.all()
        return context

    def test_func(self):
        return self.request.user.is_staff


class PublicTransportCreateView(UserPassesTestMixin, LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = PublicTransport
    template_name = "guard/views/publicTransports/index.html"
    form_class = PublicTransportForm
    success_url = reverse_lazy("guard:publicTransportsList")
    success_message = _("Public transport created successfully.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["time_formset"] = PublicTransportFormSet(self.request.POST) if self.request.POST else PublicTransportFormSet()
        return context

    def get_form(self, form_class=None):
        return _apply_transport_type_logic(super().get_form(form_class), self.request)

    def form_valid(self, form):
        context = self.get_context_data()
        time_formset = context["time_formset"]
        if time_formset.is_valid():
            has_time = any(f.cleaned_data.get("time") and not f.cleaned_data.get("DELETE", False) for f in time_formset if f.cleaned_data)
            if not has_time:
                form.add_error(None, _("Please add at least one departure time."))
                return self.form_invalid(form)
            self.object = form.save()
            time_formset.instance = self.object
            time_formset.save()
            return super().form_valid(form)
        return self.form_invalid(form)

    def test_func(self):
        return self.request.user.is_staff


class PublicTransportUpdateView(UserPassesTestMixin, LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = PublicTransport
    template_name = "guard/views/publicTransports/index.html"
    form_class = PublicTransportForm
    success_url = reverse_lazy("guard:publicTransportsList")
    success_message = _("Public transport updated successfully.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["time_formset"] = PublicTransportFormSet(self.request.POST, instance=self.object) if self.request.POST else PublicTransportFormSet(instance=self.object)
        return context

    def get_form(self, form_class=None):
        return _apply_transport_type_logic(super().get_form(form_class), self.request, self.object)

    def form_valid(self, form):
        context = self.get_context_data()
        time_formset = context["time_formset"]
        if time_formset.is_valid():
            existing = sum(1 for f in time_formset if f.instance.pk and not f.cleaned_data.get("DELETE", False))
            new      = sum(1 for f in time_formset if f.cleaned_data.get("time") and not f.instance.pk)
            if existing + new < 1:
                form.add_error(None, _("Please keep or add at least one departure time."))
                return self.form_invalid(form)
            self.object = form.save()
            time_formset.instance = self.object
            time_formset.save()
            return super().form_valid(form)
        return self.form_invalid(form)

    def test_func(self):
        return self.request.user.is_staff


class PublicTransportDeleteView(UserPassesTestMixin, LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = PublicTransport
    success_url = reverse_lazy("guard:publicTransportsList")
    success_message = _("Public transport has been deleted.")

    def delete(self, request, *args, **kwargs):
        messages.warning(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)

    def test_func(self):
        return self.request.user.is_staff


# =============================================================================
# EVENTS
# =============================================================================
class EventListView(LoginRequiredMixin, ListView):
    model = NewEvent
    template_name = "guard/views/events/list.html"
    context_object_name = "events"
    ordering = ["-created_at"]

    def get_queryset(self):
        return super().get_queryset().filter(partner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not self.request.user.is_staff:
            service = ShortIOService()
            for obj in context["events"]:
                if obj.short_id:
                    try:
                        clicks = service.get_clicks(obj.short_id)
                        if clicks != obj.clicks:
                            obj.clicks = clicks
                            obj.save(update_fields=["clicks"])
                    except Exception:
                        pass
        return context


class EventCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Event
    template_name = "guard/views/events/index.html"
    form_class = EventForm
    success_url = reverse_lazy("guard:eventsList")
    success_message = _("Event created successfully.")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["image_formset"] = ImageEventFormSet(self.request.POST, self.request.FILES) if self.request.POST else ImageEventFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        image_formset = context["image_formset"]
        if image_formset.is_valid():
            has_image = any(f.cleaned_data.get("image") and not f.cleaned_data.get("DELETE", False) for f in image_formset if f.cleaned_data)
            if not has_image:
                form.add_error(None, _("Veuillez télécharger au moins une image."))
                return self.form_invalid(form)
            self.object = form.save(commit=False)
            self.object.client = self.request.user.profile
            try:
                service = ShortIOService()
                short_data = service.shorten_url(self.object.link, title="Event Campaign")
                if short_data:
                    self.object.short_link = short_data.get("secureShortURL") or short_data.get("shortURL")
                    self.object.short_id   = short_data.get("idString")
            except Exception as e:
                logger.error(f"Short.io error: {e}")
            self.object.save()
            image_formset.instance = self.object
            image_formset.save()
            messages.success(self.request, self.success_message)
            return HttpResponseRedirect(self.get_success_url())
        return self.form_invalid(form)


class EventUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Event
    template_name = "guard/views/events/index.html"
    form_class = EventForm
    success_url = reverse_lazy("guard:eventsList")
    success_message = _("Event updated successfully.")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_queryset(self):
        return super().get_queryset().filter(client=self.request.user.profile)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["image_formset"] = ImageEventFormSet(self.request.POST, self.request.FILES, instance=self.object) if self.request.POST else ImageEventFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        image_formset = context["image_formset"]
        if image_formset.is_valid():
            existing = sum(1 for f in image_formset if f.instance.pk and not f.cleaned_data.get("DELETE", False))
            new      = sum(1 for f in image_formset if f.cleaned_data.get("image") and not f.instance.pk)
            if existing + new < 1:
                form.add_error(None, _("Veuillez conserver ou télécharger au moins une image."))
                return self.form_invalid(form)
            self.object = form.save(commit=False)
            if "link" in form.changed_data:
                try:
                    service = ShortIOService()
                    updated = False
                    if self.object.short_id:
                        result = service.update_link(self.object.short_id, self.object.link, title="Event Campaign")
                        if result:
                            self.object.short_link = result.get("secureShortURL") or result.get("shortURL")
                            updated = True
                    if not updated:
                        short_data = service.shorten_url(self.object.link, title="Event Campaign")
                        if short_data:
                            self.object.short_link = short_data.get("secureShortURL") or short_data.get("shortURL")
                            self.object.short_id   = short_data.get("idString")
                except Exception as e:
                    logger.error(f"Short.io error: {e}")
            self.object.save()
            image_formset.instance = self.object
            image_formset.save()
            messages.success(self.request, self.success_message)
            return HttpResponseRedirect(self.get_success_url())
        return self.form_invalid(form)


class EventTrackingView(UserPassesTestMixin, LoginRequiredMixin, DetailView):
    model = Event
    template_name = "guard/views/events/partials/tracking.html"
    context_object_name = "object"

    def get_queryset(self):
        return super().get_queryset().filter(client=self.request.user.profile)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        period  = self.request.GET.get("period", "today")
        context["period"]     = period
        context["page_title"] = self.object.name
        if self.object.short_id and not self.request.user.is_staff:
            context["stats"] = ShortIOService().get_link_statistics(self.object.short_id, period)
        return context

    def test_func(self):
        return not self.request.user.is_staff


class EventDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Event
    success_url = reverse_lazy("guard:eventsList")
    success_message = _("Unfortunately, this event has been deleted")

    def get_queryset(self):
        return super().get_queryset().filter(client=self.request.user.profile)

    def delete(self, request, *args, **kwargs):
        messages.warning(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)


# =============================================================================
# TIPS
# =============================================================================
class TipsListView(UserPassesTestMixin, LoginRequiredMixin, ListView):
    model = Tip
    template_name = "guard/views/tips/list.html"
    context_object_name = "tips"
    ordering = ["-created_at"]
    def test_func(self): return self.request.user.is_staff


class TipCreateView(UserPassesTestMixin, LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Tip
    form_class = TipForm
    template_name = "guard/views/tips/index.html"
    success_url = reverse_lazy("guard:tipsList")
    success_message = _("Tip created successfully")
    def form_invalid(self, form):
        messages.error(self.request, _("Error creating tip. Please check the form."))
        return super().form_invalid(form)
    def test_func(self): return self.request.user.is_staff


class TipUpdateView(UserPassesTestMixin, LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Tip
    form_class = TipForm
    template_name = "guard/views/tips/index.html"
    success_url = reverse_lazy("guard:tipsList")
    success_message = _("Tip updated successfully")
    def form_invalid(self, form):
        messages.error(self.request, _("Error updating tip. Please check the form."))
        return super().form_invalid(form)
    def test_func(self): return self.request.user.is_staff


class TipDeleteView(UserPassesTestMixin, LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Tip
    success_url = reverse_lazy("guard:tipsList")
    success_message = _("Tip deleted successfully")
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)
    def test_func(self): return self.request.user.is_staff


# =============================================================================
# HIKING
# =============================================================================
class HikingListView(UserPassesTestMixin, LoginRequiredMixin, ListView):
    model = Hiking
    template_name = "guard/views/hiking/list.html"
    context_object_name = "hikings"
    ordering = ["-created_at"]
    def test_func(self): return self.request.user.is_staff


class HikingCreateView(UserPassesTestMixin, LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Hiking
    form_class = HikingForm
    template_name = "guard/views/hiking/index.html"
    success_url = reverse_lazy("guard:hikingsList")
    success_message = _("Hiking created successfully")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["image_formset"]    = ImageHikingFormSet(self.request.POST, self.request.FILES)
            context["location_formset"] = HikingLocationFormSet(self.request.POST)
        else:
            context["image_formset"]    = ImageHikingFormSet()
            context["location_formset"] = HikingLocationFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        image_formset    = context["image_formset"]
        location_formset = context["location_formset"]
        if image_formset.is_valid() and location_formset.is_valid():
            has_image = any(f.cleaned_data.get("image") and not f.cleaned_data.get("DELETE", False) for f in image_formset if f.cleaned_data)
            if not has_image:
                form.add_error(None, _("Please upload at least one image."))
                return self.form_invalid(form)
            self.object = form.save()
            image_formset.instance    = self.object
            location_formset.instance = self.object
            image_formset.save()
            location_formset.save()
            return super().form_valid(form)
        return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, _("Error creating hiking. Please check the form."))
        return super().form_invalid(form)
    def test_func(self): return self.request.user.is_staff


class HikingUpdateView(UserPassesTestMixin, LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Hiking
    form_class = HikingForm
    template_name = "guard/views/hiking/index.html"
    success_url = reverse_lazy("guard:hikingsList")
    success_message = _("Hiking updated successfully")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["image_formset"]    = ImageHikingFormSet(self.request.POST, self.request.FILES, instance=self.object)
            context["location_formset"] = HikingLocationFormSet(self.request.POST, instance=self.object)
        else:
            context["image_formset"]    = ImageHikingFormSet(instance=self.object)
            context["location_formset"] = HikingLocationFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        image_formset    = context["image_formset"]
        location_formset = context["location_formset"]
        if image_formset.is_valid() and location_formset.is_valid():
            existing = sum(1 for f in image_formset if f.instance.pk and not f.cleaned_data.get("DELETE", False))
            new      = sum(1 for f in image_formset if f.cleaned_data.get("image") and not f.instance.pk)
            if existing + new < 1:
                form.add_error(None, _("Veuillez conserver ou télécharger au moins une image."))
                return self.form_invalid(form)
            self.object = form.save()
            image_formset.instance    = self.object
            location_formset.instance = self.object
            image_formset.save()
            location_formset.save()
            return super().form_valid(form)
        return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, _("Error updating hiking. Please check the form."))
        return super().form_invalid(form)
    def test_func(self): return self.request.user.is_staff


class HikingDeleteView(UserPassesTestMixin, LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Hiking
    success_url = reverse_lazy("guard:hikingsList")
    success_message = _("Hiking deleted successfully")
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)
    def test_func(self): return self.request.user.is_staff


# =============================================================================
# ADS — LISTE
# =============================================================================
class AdListView(LoginRequiredMixin, ListView):
    model = Ad
    template_name = "guard/views/ads/list.html"
    context_object_name = "ads"
    ordering = ["-created_at"]

    def get_queryset(self):
        return super().get_queryset().filter(client=self.request.user.profile)


# =============================================================================
# ADS — CRÉATION
# =============================================================================
class AdCreateView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'guard/views/ads/form.html', {'form': AdForm()})

    def post(self, request):
        form    = AdForm(request.POST, request.FILES)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if form.is_valid():
            ad             = form.save(commit=False)
            ad.client      = request.user.profile
            ad.total_price = form.cleaned_data.get('total_price', Decimal('0'))
            ad.save()
            if is_ajax:
                return JsonResponse({'ok': True, 'ad_id': ad.pk})
            messages.success(request, _("Pub créée. Complétez le paiement pour l'activer."))
            return redirect('guard:adsList')

        if is_ajax:
            return JsonResponse({'ok': False, 'errors': {f: e.get_json_data() for f, e in form.errors.items()}}, status=400)

        return render(request, 'guard/views/ads/form.html', {'form': form})


# =============================================================================
# ADS — MODIFICATION (bloquée si payée)
# =============================================================================
class AdUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model           = Ad
    form_class      = AdForm
    template_name   = "guard/views/ads/form.html"
    success_url     = reverse_lazy("guard:adsList")
    success_message = _("Pub mise à jour avec succès")

    def dispatch(self, request, *args, **kwargs):
        ad = self.get_object()
        if ad.is_paid:
            messages.error(request, _("Cette pub est verrouillée après paiement. Aucune modification possible."))
            return redirect('guard:adsList')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(client=self.request.user.profile)

    def form_valid(self, form):
        self.object             = form.save(commit=False)
        self.object.total_price = form.cleaned_data.get('total_price', self.object.total_price)
        is_ajax = self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if "link" in form.changed_data:
            try:
                service = ShortIOService()
                updated = False
                if self.object.short_id:
                    result = service.update_link(self.object.short_id, self.object.link, title="Ad Campaign")
                    if result:
                        self.object.short_link = result.get("secureShortURL") or result.get("shortURL")
                        updated = True
                if not updated:
                    short_data = service.shorten_url(self.object.link, title="Ad Campaign")
                    if short_data:
                        self.object.short_link = short_data.get("secureShortURL") or short_data.get("shortURL")
                        self.object.short_id   = short_data.get("idString")
                        self.object.clicks     = 0
            except Exception as e:
                logger.error(f"Short.io error: {e}")

        self.object.save()
        if is_ajax:
            return JsonResponse({'ok': True, 'ad_id': self.object.pk})

        messages.success(self.request, self.success_message)
        return HttpResponseRedirect(self.get_success_url())


# =============================================================================
# ADS — SUPPRESSION
# =============================================================================
class AdDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model       = Ad
    success_url = reverse_lazy("guard:adsList")
    success_message = _("Ad deleted successfully")

    def get_queryset(self):
        return super().get_queryset().filter(client=self.request.user.profile)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)


# =============================================================================
# ADS — TRACKING
# =============================================================================
class AdTrackingView(UserPassesTestMixin, LoginRequiredMixin, DetailView):
    model = Ad
    template_name = "guard/views/ads/partials/tracking.html"
    context_object_name = "object"

    def get_queryset(self):
        return super().get_queryset().filter(client=self.request.user.profile)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        period  = self.request.GET.get("period", "today")
        context["period"]     = period
        context["page_title"] = self.object.link
        if self.object.short_id and not self.request.user.is_staff:
            context["stats"] = ShortIOService().get_link_statistics(self.object.short_id, period)
        return context

    def test_func(self):
        return not self.request.user.is_staff


# =============================================================================
# ADS — KONNECT : CRÉER LE PAIEMENT
# =============================================================================
class CreateCheckoutSessionView(LoginRequiredMixin, View):

    DAILY_RATE_TND = Decimal('15.000')

    def post(self, request, pk, *args, **kwargs):
        ad = get_object_or_404(Ad, pk=pk, client=request.user.profile)

        if ad.is_paid:
            return JsonResponse({'error': 'Cette pub est déjà payée.'}, status=400)
        if not ad.startDate or not ad.endDate:
            return JsonResponse({'error': 'Les dates ne sont pas définies.'}, status=400)

        today = timezone.now().date()
        if ad.startDate <= today:
            return JsonResponse({'error': 'La date de début doit être demain au minimum.'}, status=400)
        if ad.endDate <= ad.startDate:
            return JsonResponse({'error': 'La date de fin doit être après la date de début.'}, status=400)

        days           = (ad.endDate - ad.startDate).days
        ad.total_price = Decimal(str(days)) * self.DAILY_RATE_TND
        ad.save(update_fields=['total_price'])

        # ── MODE TEST : confirme le paiement directement sans Konnect ──
        # Quand tu auras les clés Konnect, remplace ce bloc par le vrai appel API
        ad.is_paid = True
        ad.sync_status()
        ad.save(update_fields=['is_paid', 'status'])

        success_url = request.build_absolute_uri(
            f'/guard/ads/{ad.pk}/confirm-payment/?payment_ref=TEST-{ad.pk}'
        )
        return JsonResponse({'url': success_url})


# =============================================================================
# ADS — KONNECT : WEBHOOK
# =============================================================================
@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):

    def post(self, request, *args, **kwargs):
        import json
        try:
            data        = json.loads(request.body)
            payment_ref = data.get("payment_ref") or data.get("paymentRef") or data.get("ref")
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Konnect webhook : body invalide — {e}")
            return HttpResponse(status=400)

        if not payment_ref:
            logger.warning("Konnect webhook : payment_ref manquant")
            return HttpResponse(status=400)

        service          = KonnectService()
        confirmed_status = service.get_payment_status(payment_ref)

        if confirmed_status == "completed":
            try:
                ad         = Ad.objects.get(payment_ref=payment_ref)
                ad.is_paid = True
                ad.sync_status()
                ad.save(update_fields=['is_paid', 'status'])
                logger.info(f"Pub {ad.pk} confirmée via webhook Konnect.")
            except Ad.DoesNotExist:
                logger.error(f"Webhook Konnect : aucune pub avec payment_ref={payment_ref}")

        return HttpResponse(status=200)


# =============================================================================
# ADS — KONNECT : CONFIRMATION (success_url)
# =============================================================================
class AdConfirmPaymentView(LoginRequiredMixin, View):

    def get(self, request, pk, *args, **kwargs):
        payment_ref = request.GET.get('payment_ref') or request.GET.get('paymentRef')
        ad          = get_object_or_404(Ad, pk=pk, client=request.user.profile)

        if payment_ref and not ad.is_paid:
            service = KonnectService()
            status  = service.get_payment_status(payment_ref)
            if status == "completed":
                ad.is_paid     = True
                ad.payment_ref = payment_ref
                ad.sync_status()
                ad.save(update_fields=['is_paid', 'status', 'payment_ref'])

        # Mode test : payment_ref commence par TEST-
        if payment_ref and payment_ref.startswith('TEST-') and not ad.is_paid:
            ad.is_paid = True
            ad.sync_status()
            ad.save(update_fields=['is_paid', 'status'])

        if ad.is_paid:
            messages.success(request, _("Paiement confirmé ! Votre pub est maintenant active et verrouillée."))
        else:
            messages.warning(request, _("Le paiement est en cours de traitement. Veuillez patienter."))

        return redirect('guard:adsList')


# =============================================================================
# ADS — TABLEAU DE BORD
# =============================================================================
class AdsDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "guard/views/ads/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx     = super().get_context_data(**kwargs)
        profile = self.request.user.profile
        today   = timezone.now().date()

        Ad.objects.filter(client=profile, is_paid=True, endDate__lt=today).exclude(status=Ad.Status.FINISHED).update(status=Ad.Status.FINISHED)

        qs = Ad.objects.filter(client=profile)
        ctx['total_ads']    = qs.count()
        ctx['active_ads']   = qs.filter(status=Ad.Status.ACTIVE).count()
        ctx['finished_ads'] = qs.filter(status=Ad.Status.FINISHED).count()
        ctx['pending_ads']  = qs.filter(status=Ad.Status.PENDING_PAYMENT).count()
        ctx['total_clicks'] = qs.aggregate(t=Sum(F('db_clicks_count') + F('clicks')))['t'] or 0
        ctx['total_spent']  = qs.filter(is_paid=True).aggregate(t=Sum('total_price'))['t'] or Decimal('0')
        ctx['recent_ads']   = qs.order_by('-created_at')[:10]
        return ctx


# =============================================================================
# PARTNERS
# =============================================================================
class PartnerListView(UserPassesTestMixin, LoginRequiredMixin, ListView):
    model = Partner; template_name = "guard/views/partners/list.html"
    context_object_name = "partners"; ordering = ["-id"]
    def test_func(self): return self.request.user.is_staff
class PartnerCreateView(CreateView):
    model = Partner
    form_class = PartnerForm
    template_name = 'guard/views/partners/index.html'
    success_url = reverse_lazy('guard:partnersList')

    def form_valid(self, form):
    # 1. Isavi el Partner (name, email, logo...) f-el base
        self.object = form.save()
    
    # 2. EB3ATH L-EMAIL
        try:
            send_validation_email(self.object)
        except Exception as e:
            print(f"Erreur d'envoi email: {e}")

    # 3. Yajbed el list mte3 el locations elli selectionnahom f-el form
        selected_locations = form.cleaned_data.get('locations')
    
    # 4. Reset el locations el 9dom
        Location.objects.filter(partner=self.object).update(partner=None)

    # 5. Assign el locations el jdod
        if selected_locations:
            selected_locations.update(partner=self.object)
        
        return super().form_valid(form)
class PartnerUpdateView(UserPassesTestMixin, LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Partner
    form_class = PartnerForm
    template_name = "guard/views/partners/index.html"
    success_url = reverse_lazy("guard:partnersList")
    success_message = _("Partner updated successfully.")

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        # 1. Savi el modifs el jdod mte3 el partner
        self.object = form.save()
        
        # 2. (Facultatif) T-najem t3awed tba3th email ken t7eb 
        # sinon na77i hal zouz stour:
        # from .utils import send_partner_verification_email
        # send_partner_verification_email(self.object, self.request)

        # 3. Logic mte3 el Locations (MHEMA BARCHA)
        selected_locations = form.cleaned_data.get('locations')
        
        # Reseti el locations elli kenou m3ah 9bal
        from .models import Location
        Location.objects.filter(partner=self.object).update(partner=None)

        # Erbet el locations el jdod elli t-selectew f-el formulaire
        if selected_locations:
            selected_locations.update(partner=self.object)
            
        return super().form_valid(form)

class PartnerDeleteView(UserPassesTestMixin, LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Partner; template_name = "guard/views/partners/delete.html"
    success_url = reverse_lazy("guard:partnersList"); success_message = _("Partner deleted successfully.")
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message); return super().delete(request, *args, **kwargs)
    def test_func(self): return self.request.user.is_staff


# =============================================================================
# SPONSORS
# =============================================================================
class SponsorListView(UserPassesTestMixin, LoginRequiredMixin, ListView):
    model = Sponsor; template_name = "guard/views/sponsors/list.html"
    context_object_name = "sponsors"; ordering = ["-id"]
    def test_func(self): return self.request.user.is_staff

class SponsorCreateView(UserPassesTestMixin, LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Sponsor; form_class = SponsorForm; template_name = "guard/views/sponsors/index.html"
    success_url = reverse_lazy("guard:sponsorsList"); success_message = _("Sponsor created successfully.")
    def test_func(self): return self.request.user.is_staff

class SponsorUpdateView(UserPassesTestMixin, LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Sponsor; form_class = SponsorForm; template_name = "guard/views/sponsors/index.html"
    success_url = reverse_lazy("guard:sponsorsList"); success_message = _("Sponsor updated successfully.")
    def test_func(self): return self.request.user.is_staff

class SponsorDeleteView(UserPassesTestMixin, LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Sponsor; template_name = "guard/views/sponsors/delete.html"
    success_url = reverse_lazy("guard:sponsorsList"); success_message = _("Sponsor deleted successfully.")
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message); return super().delete(request, *args, **kwargs)
    def test_func(self): return self.request.user.is_staff


# =============================================================================
# API HELPERS
# =============================================================================
@login_required
def get_cities_by_country(request, country_id):
    from cities_light.models import City
    return JsonResponse({"success": True, "cities": list(City.objects.filter(country_id=country_id).values("id", "name"))})

@login_required
def get_subregions_by_city(request, city_id):
    from cities_light.models import City, SubRegion
    try:
        city = City.objects.get(id=city_id)
        return JsonResponse({"success": True, "subregions": list(SubRegion.objects.filter(region=city.region).values("id", "name"))})
    except City.DoesNotExist:
        return JsonResponse({"success": False, "error": "City not found"}, status=404)

@login_required
def get_locations_by_city(request, city_id):
    try:
        return JsonResponse({"success": True, "locations": list(Location.objects.filter(city_id=city_id).values("id", "name_en", "name_fr"))})
    except Exception:
        return JsonResponse({"success": False, "error": "Error fetching locations"}, status=500)




def verify_partner_email(request):
    token = request.GET.get('token')
    if not token:
        return HttpResponse("Token manquant", status=400)

    try:
        # On décode le token (validité de 48h = 172800 secondes)
        data = signing.loads(token, max_age=172800)
        partner_id = data.get('partner_id')
        
        # On récupère le partenaire et on le valide
        partner = Partner.objects.get(id=partner_id)
        if not partner.is_verified:
            partner.is_verified = True
            partner.save()
            return render(request, 'verification_success.html', {'name': partner.name})
        else:
            return HttpResponse("Compte déjà vérifié.")

    except (signing.SignatureExpired, signing.BadSignature):
        return HttpResponse("Le lien est invalide ou a expiré.", status=400)