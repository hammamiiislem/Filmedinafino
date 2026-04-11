from django.urls import path, include

from .views import (
    DashboardView,
    SubscribersListView,
    LocationsListView,
    LocationCreateView,
    LocationUpdateView,
    LocationDeleteView,
    EventListView,
    EventCreateView,
    EventUpdateView,
    EventDeleteView,
    TipsListView,
    TipCreateView,
    TipUpdateView,
    TipDeleteView,
    HikingListView,
    HikingCreateView,
    HikingUpdateView,
    HikingDeleteView,
    AdListView,
    AdCreateView,
    AdUpdateView,
    AdDeleteView,
    AdsDashboardView,
    CreateCheckoutSessionView,
    AdConfirmPaymentView,
    StripeWebhookView,
    EventTrackingView,
    AdTrackingView,
    PublicTransportListView,
    PublicTransportCreateView,
    PublicTransportUpdateView,
    PublicTransportDeleteView,
    PartnerListView,
    PartnerCreateView,
    PartnerUpdateView,
    PartnerDeleteView,
    SponsorListView,
    SponsorCreateView,
    SponsorUpdateView,
    SponsorDeleteView,
    get_cities_by_country,
    get_subregions_by_city,
    get_locations_by_city,
    DashboardStatsAPIView,
    record_ad_click,
    record_event_click,
)
from .views import verify_partner_email

app_name = "guard"

urlpatterns = [
    # ── Tableau de bord principal ─────────────────────────────────────────────
    path("", DashboardView.as_view(), name="dashboard"),

    # ── Section staff ─────────────────────────────────────────────────────────
    path(
        "staff/",
        include([
            path("subscribersList/",        SubscribersListView.as_view(),       name="subscribersList"),

            path("locationsList/",          LocationsListView.as_view(),         name="locationsList"),
            path("locations/create/",       LocationCreateView.as_view(),        name="location_create"),
            path("locations/update/<int:pk>/", LocationUpdateView.as_view(),     name="location_update"),
            path("locations/delete/<int:pk>/", LocationDeleteView.as_view(),     name="location_delete"),

            path("eventsList/",             EventListView.as_view(),             name="eventsList"),
            path("events/create/",          EventCreateView.as_view(),           name="event_create"),
            path("events/update/<int:pk>/", EventUpdateView.as_view(),           name="event_update"),
            path("events/delete/<int:pk>/", EventDeleteView.as_view(),           name="event_delete"),
            path("events/track/<int:pk>/",  EventTrackingView.as_view(),         name="event_track"),

            path("tips/",                   TipsListView.as_view(),              name="tipsList"),
            path("tips/create/",            TipCreateView.as_view(),             name="tip_create"),
            path("tips/update/<int:pk>/",   TipUpdateView.as_view(),             name="tip_update"),
            path("tips/delete/<int:pk>/",   TipDeleteView.as_view(),             name="tip_delete"),

            path("hikings/",                HikingListView.as_view(),            name="hikingsList"),
            path("hikings/create/",         HikingCreateView.as_view(),          name="hiking_create"),
            path("hikings/update/<int:pk>/", HikingUpdateView.as_view(),         name="hiking_update"),
            path("hikings/delete/<int:pk>/", HikingDeleteView.as_view(),         name="hiking_delete"),

            path("publicTransportsList/",   PublicTransportListView.as_view(),   name="publicTransportsList"),
            path("publicTransports/create/", PublicTransportCreateView.as_view(), name="publicTransport_create"),
            path("publicTransports/update/<int:pk>/", PublicTransportUpdateView.as_view(), name="publicTransport_update"),
            path("publicTransports/delete/<int:pk>/", PublicTransportDeleteView.as_view(), name="publicTransport_delete"),

            path("partners/",               PartnerListView.as_view(),           name="partnersList"),
            path("partners/create/",        PartnerCreateView.as_view(),         name="partner_create"),
            path("partners/update/<int:pk>/", PartnerUpdateView.as_view(),       name="partner_update"),
            path("partners/delete/<int:pk>/", PartnerDeleteView.as_view(),       name="partner_delete"),

            path("sponsors/",               SponsorListView.as_view(),           name="sponsorsList"),
            path("sponsors/create/",        SponsorCreateView.as_view(),         name="sponsor_create"),
            path("sponsors/update/<int:pk>/", SponsorUpdateView.as_view(),       name="sponsor_update"),
            path("sponsors/delete/<int:pk>/", SponsorDeleteView.as_view(),       name="sponsor_delete"),
        ]),
    ),

    # ── Pubs (Ads) ───────────────────────────────────────────────────────────
    path("adsList/",                    AdListView.as_view(),                name="adsList"),
    path("ads/create/",                 AdCreateView.as_view(),              name="ad_create"),
    path("ads/update/<int:pk>/",        AdUpdateView.as_view(),              name="ad_update"),
    path("ads/delete/<int:pk>/",        AdDeleteView.as_view(),              name="ad_delete"),
    path("ads/track/<int:pk>/",         AdTrackingView.as_view(),            name="ad_track"),
    path("ads/dashboard/",              AdsDashboardView.as_view(),          name="ads_dashboard"),

    # ── Stripe ───────────────────────────────────────────────────────────────
    path("ads/<int:pk>/create-checkout/",  CreateCheckoutSessionView.as_view(), name="ad_create_checkout"),
    path("ads/<int:pk>/confirm-payment/",  AdConfirmPaymentView.as_view(),      name="ad_confirm_payment"),
    path("webhooks/stripe/",               StripeWebhookView.as_view(),         name="stripe_webhook"),

    # ── API ──────────────────────────────────────────────────────────────────
    path("api/cities/<int:country_id>/",       get_cities_by_country,           name="get_cities_by_country"),
    path("api/subregions/<int:city_id>/",      get_subregions_by_city,          name="get_subregions_by_city"),
    path("api/locations/<int:city_id>/",       get_locations_by_city,           name="get_locations_by_city"),
    path("api/dashboard/stats/",               DashboardStatsAPIView.as_view(), name="dashboard_stats_api"),
    path("api/record/ad/<int:ad_id>/",         record_ad_click,                 name="record_ad_click"),
    path("api/record/event/<int:event_id>/",   record_event_click,              name="record_event_click"),
    path('verify-email/', verify_partner_email, name='verify-email'),
]