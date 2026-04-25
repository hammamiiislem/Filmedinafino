import os
from io import BytesIO
from PIL import Image as PilImage
from django.core.files.base import ContentFile
from django.core import signing 
# --- LES AJOUTS ICI ---
from django.core.mail import send_mail
from django.conf import settings
from django.utils.translation import activate, gettext as _

def optimize_image(image_field, resize_width=None):
    """
    Optimizes a django ImageField file:
    - Converts to RGB
    - Optionally resizes (if resize_width provided and width > resize_width)
    - Compresses to JPEG (quality=80)

    Args:
        image_field: The Django ImageField file object
        resize_width: Optional integer width to resize down to

    Returns:
        tuple (filename, ContentFile) if optimized successfully
        None if no processing needed or error
    """
    if not image_field:
        return None

    try:
        # Open image using Pillow
        img = PilImage.open(image_field)

        # Convert to RGB (standard for JPEG)
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Resize if requested and needed
        if resize_width and img.width > resize_width:
            ratio = resize_width / float(img.width)
            height = int((float(img.height) * float(ratio)))
            img = img.resize((resize_width, height), PilImage.Resampling.LANCZOS)

        # Save to buffer
        output = BytesIO()
        img.save(output, format="JPEG", quality=80, optimize=True)
        output.seek(0)

        # Generate new filename
        original_name = os.path.basename(image_field.name)
        name_base, _ = os.path.splitext(original_name)

        # Clean up filename (avoid double extensions like image.png.jpg)
        if name_base.lower().endswith(".jpg") or name_base.lower().endswith(".jpeg"):
            pass

        new_filename = f"{name_base}.jpg"

        return new_filename, ContentFile(output.read())

    except Exception as e:
        # In case of error (e.g. invalid image file), return None
        print(f"Error optimizing image: {e}")
        return None


def resize_to_fixed(image_field, size=(300, 200)):
    """
    Resizes an image to a fixed size while maintaining aspect ratio and cropping.
    """
    if not image_field:
        return None

    try:
        from PIL import ImageOps
        img = PilImage.open(image_field)

        # Convert to RGB
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Resize and crop to fit exactly the target size
        img = ImageOps.fit(img, size, PilImage.Resampling.LANCZOS)

        # Save to buffer
        output = BytesIO()
        img.save(output, format="JPEG", quality=80, optimize=True)
        output.seek(0)

        # Generate new filename
        original_name = os.path.basename(image_field.name)
        name_base, _ = os.path.splitext(original_name)
        new_filename = f"{name_base}.jpg"

        return new_filename, ContentFile(output.read())

    except Exception as e:
        print(f"Error resizing image: {e}")
        return None



def send_validation_email(partner, plain_password=None, lang='fr'):
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string
 
    activate(lang)
 
    token = signing.dumps({'partner_id': partner.id})
    verify_url = f"{settings.SITE_URL}/verify-email/?token={token}"
 
    context = {
        'company_name': partner.name,
        'verification_url': verify_url,
        'username': getattr(partner, 'username', None) or partner.name,  # ← CORRIGÉ
        'password': plain_password,
        'icon_url': f"{settings.SITE_URL}/static/icon.png",
    }   
    subject = _("Validez votre compte FielMedina — %(partner_name)s") % {'partner_name': partner.name}
    text_content = render_to_string('emails/verification.txt', context)
    html_content = render_to_string('emails/verification.html', context)
 
    email = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [partner.email],
    )
    email.attach_alternative(html_content, "text/html")
 
    try:
        email.send(fail_silently=False)
        print(f"DEBUG: Email envoyé à {partner.email}")
    except Exception as e:
        print(f"Erreur d'envoi email : {e}")