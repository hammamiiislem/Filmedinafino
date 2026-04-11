from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from strawberry.django.views import AsyncGraphQLView
from api.schema import schema

admin_url = f"{settings.DJANGO_ADMIN_URL.strip('/')}/"

urlpatterns = [
    path(admin_url, admin.site.urls),
    path("tinymce/", include("tinymce.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
    path("", include("api.urls")),
    path('events/', include('events.urls', namespace='events')),
    path('', include('guard.urls', namespace='guard')),
    path("", include("shared.urls")),
    path("graphql/", AsyncGraphQLView.as_view(schema=schema)),
]
   


urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
