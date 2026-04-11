import os
import django
import json
from django.test import RequestFactory
from django.contrib.auth.models import User

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from guard.views import DashboardStatsAPIView

factory = RequestFactory()
user = User.objects.filter(is_superuser=True).first()
if not user:
    user = User.objects.create_superuser('temp_admin', 'admin@example.com', 'pass')

request = factory.get('/api/dashboard/stats/')
request.user = user

view = DashboardStatsAPIView.as_view()
response = view(request)
print(response.content.decode())
