import os
import django
from django.conf import settings
from django.core.mail import send_mail
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

print("Testing SMTP connection...")
start_time = time.time()
try:
    send_mail(
        'Test Subject',
        'Test Message',
        settings.DEFAULT_FROM_EMAIL,
        ['islemhamami345@gmail.com'], # Sending to himself to test
        fail_silently=False,
    )
    print(f"Email sent successfully in {time.time() - start_time:.2f} seconds!")
except Exception as e:
    print(f"Failed to send email: {e}")
