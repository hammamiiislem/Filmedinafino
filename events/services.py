from django.core.exceptions import ValidationError, PermissionDenied
from django.utils.translation import gettext as _
from django.utils import timezone
from datetime import timedelta
from .models import Event, EventMedia


# ✅ Validation
def validate_event_submission(start_date):
    """Enforce that events must be submitted at least 7 days before the start date."""
    if not start_date:
        raise ValidationError(_("Start date is required"))
    
    # Handle both date and datetime
    if hasattr(start_date, 'date'):
        start_date_val = start_date.date()
    else:
        start_date_val = start_date

    now = timezone.now().date()
    lead_time = start_date_val - now
    if lead_time < timedelta(days=7):
        raise ValidationError(_("Events must be submitted at least 7 days before the start date."))


def validate_event_dates(start_date, end_date):
    if end_date <= start_date:
        raise ValidationError(_("End date must be after start date"))


def validate_required_fields(title, start_date, end_date):
    if not title:
        raise ValidationError(_("Title is required"))
    if not start_date or not end_date:
        raise ValidationError(_("Dates are required"))


def check_partner_ownership(user, event):
    if event.partner != user and not user.is_staff:
        raise PermissionDenied(_("You do not have permission"))


def initiate_event_payment(user, event_data):
    """
    Initiates a Konnect payment for the event.
    Returns the payment URL and reference.
    """
    from guard.views import KonnectService
    import uuid
    
    service = KonnectService()
    amount = 50000 # Exemple: 50 TND (en millimes)
    order_id = f"EVT-{uuid.uuid4().hex[:8]}"
    
    # In a real scenario, success_url should point to a callback that finalizes creation
    success_url = "http://localhost:8000/events/payment/callback/?status=success"
    fail_url = "http://localhost:8000/events/payment/callback/?status=fail"
    
    payment_data = service.create_payment(
        amount_millimes=amount,
        description=f"Payment for event: {event_data.get('title')}",
        order_id=order_id,
        success_url=success_url,
        fail_url=fail_url
    )
    
    return payment_data


def create_event(user, data, payment_ref=None):
    validate_required_fields(
        data.get("title"),
        data.get("start_date"),
        data.get("end_date")
    )

    validate_event_dates(
        data.get("start_date"),
        data.get("end_date")
    )
    
    validate_event_submission(data.get("start_date"))

    event = Event.objects.create(
        partner=user,
        title=data.get("title"),
        description=data.get("description", ""),
        start_date=data.get("start_date"),
        end_date=data.get("end_date"),
        registration_link=data.get("registration_link"),
        location=data.get("location"),
        status='PENDING_APPROVAL' if payment_ref else 'PENDING_PAYMENT',
        payment_ref=payment_ref
    )

    return event


def update_event(user, event_id, data):
    event = Event.objects.get(id=event_id)
    check_partner_ownership(user, event)

    # Bloquer l'édition si déjà approuvé
    if event.status == 'APPROVED' and not user.is_staff:
        raise PermissionDenied(_("Approved events cannot be edited."))

    if "start_date" in data and "end_date" in data:
        validate_event_dates(data["start_date"], data["end_date"])
        validate_event_submission(data["start_date"])

    for field, value in data.items():
        setattr(event, field, value)

    event.save()
    return event


def delete_event(user, event_id):
    event = Event.objects.get(id=event_id)
    check_partner_ownership(user, event)
    event.delete()
    return True


def upload_event_media(user, event_id, file, media_type):
    event = Event.objects.get(id=event_id)
    check_partner_ownership(user, event)

    if media_type not in ["IMAGE", "VIDEO"]:
        raise ValidationError(_("Invalid media type"))

    media = EventMedia.objects.create(
        event=event,
        file=file,
        type=media_type
    )
    return media


def approve_event(admin_user, event_id):
    if not admin_user.is_staff:
        raise PermissionDenied(_("Only admin can approve events"))
    
    event = Event.objects.get(id=event_id)
    event.status = 'APPROVED'
    event.save()
    return event


def reject_event(admin_user, event_id):
    if not admin_user.is_staff:
        raise PermissionDenied(_("Only admin can reject events"))
    
    event = Event.objects.get(id=event_id)
    event.status = 'REJECTED'
    event.save()
    return event