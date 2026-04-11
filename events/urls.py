from django.urls import path
from .views import EventPaymentInitiateView, EventPaymentCallbackView, EventCreateView, EventUpdateView, EventDeleteView

app_name = 'events'

urlpatterns = [
    path('create/', EventCreateView.as_view(), name='create'),
    path('payment/initiate/', EventPaymentInitiateView.as_view(), name='payment_initiate'),
    path('payment/callback/', EventPaymentCallbackView.as_view(), name='payment_callback'),
    path('update/<uuid:pk>/', EventUpdateView.as_view(), name='update'),
    path('delete/<uuid:pk>/', EventDeleteView.as_view(), name='delete'),
]
