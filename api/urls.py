from django.urls import path
from django.conf import settings
from strawberry.django.views import GraphQLView
from .schema import schema
from django.views.decorators.csrf import csrf_exempt
from guard import views as guard_views 
from api.schema import schema
from strawberry.django.views import AsyncGraphQLView

urlpatterns = [
    path("graphql/", csrf_exempt(AsyncGraphQLView.as_view(schema=schema))),
    path('partners/create/', guard_views.PartnerCreateView.as_view(), name='partner_create'),
    path('partners/', guard_views.PartnerListView.as_view(), name='partnersList'),
]
