from django.core.mail import send_mail
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.template.loader import render_to_string

def send_partner_verification_email(partner, request):
    token = default_token_generator.make_token(partner)
    uid = urlsafe_base64_encode(force_bytes(partner.pk))
    
    # Link mrigel
    verification_url = request.build_absolute_uri(
        reverse('guard:verify_partner', kwargs={'uidb64': uid, 'token': token})
    )
    
    subject = "FielMedina - Validation de votre compte"
    message = f"Bonjour {partner.name},\n\nCliquer ici pour valider: {verification_url}"
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [partner.email],
        fail_silently=False,
    )