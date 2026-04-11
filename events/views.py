from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext as _

from .forms import EventForm
from .models import Event
from .services import initiate_event_payment, create_event
from guard.views import KonnectService


class EventPaymentInitiateView(LoginRequiredMixin, View):
    """
    Step 1: Show the premium payment gate.
    """
    def get(self, request):
        return render(request, 'events/payment_gate.html')

    def post(self, request):
        # Step 1.5: Initiate the payment on POST
        payment_data = initiate_event_payment(request.user, {"title": "New Event Creation"})
        
        if payment_data and "payment_url" in payment_data:
            return redirect(payment_data["payment_url"])
        
        messages.error(request, _("Unable to initiate payment. Please try again later."))
        return redirect('guard:dashboard')


class EventPaymentCallbackView(LoginRequiredMixin, View):
    """
    Step 2: Handle the return from Konnect.
    """
    def get(self, request):
        payment_ref = request.GET.get('paymentRef')
        status = request.GET.get('status') # This depends on how Konnect redirects
        
        # MOCK logic: If we are in mock mode, we assume it's okay if status=success
        # In production, we should call get_payment_status
        service = KonnectService()
        
        # Only verify if we have a payment_ref
        if payment_ref:
            # For the demo, if it starts with 'MOCK-', it's success
            if payment_ref.startswith('MOCK-') or service.get_payment_status(payment_ref) == 'completed':
                request.session['event_payment_verified'] = True
                request.session['event_payment_ref'] = payment_ref
                messages.success(request, _("Payment successful! You can now create your event."))
                return redirect('events:create')
        
        messages.error(request, _("Payment failed or was cancelled."))
        return redirect('guard:dashboard')


class EventCreateView(LoginRequiredMixin, View):
    """
    Step 3: The actual form, gated by payment verification.
    """
    def get(self, request):
        if not request.session.get('event_payment_verified'):
            messages.warning(request, _("You must pay before creating an event."))
            return redirect('events:payment_initiate')
        
        form = EventForm()
        return render(request, 'events/create.html', {'form': form})

    def post(self, request):
        if not request.session.get('event_payment_verified'):
             return redirect('events:payment_initiate')
        
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            payment_ref = request.session.get('event_payment_ref')
            event = create_event(request.user, form.cleaned_data, payment_ref=payment_ref)
            
            # Clear session
            del request.session['event_payment_verified']
            del request.session['event_payment_ref']
            
            messages.success(request, _("Event submitted and pending admin approval."))
            return redirect('guard:dashboard')
        
        return render(request, 'events/create.html', {'form': form})


class EventUpdateView(LoginRequiredMixin, View):
    def get(self, request, pk):
        event = Event.objects.get(pk=pk, partner=request.user)
        if event.status == 'APPROVED':
            messages.warning(request, _("Approved events cannot be edited."))
            return redirect('guard:dashboard')
        
        form = EventForm(instance=event)
        return render(request, 'events/create.html', {'form': form, 'is_update': True})

    def post(self, request, pk):
        event = Event.objects.get(pk=pk, partner=request.user)
        if event.status == 'APPROVED':
             return redirect('guard:dashboard')
        
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, _("Event updated successfully."))
            return redirect('guard:dashboard')
        return render(request, 'events/create.html', {'form': form, 'is_update': True})


class EventDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        event = Event.objects.get(pk=pk, partner=request.user)
        event.delete()
        messages.success(request, _("Event deleted successfully."))
        return redirect('guard:dashboard')
