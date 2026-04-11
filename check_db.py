import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from guard.models import Location, LocationCategory
from cities_light.models import City, Country

tunisia = Country.objects.get(name='Tunisia')
cities_to_check = ["Kairouan", "Mahdia", "Monastir", "Sfax", "Sousse", "Tunis"]

print("--- Cities ---")
for city_name in cities_to_check:
    city = City.objects.filter(country=tunisia, name__iexact=city_name).first()
    if city:
        count = Location.objects.filter(city=city).count()
        print(f"{city.name} (ID: {city.id}): {count} locations")
    else:
        print(f"{city_name}: Not found")

print("\n--- Categories ---")
for cat in LocationCategory.objects.all():
    print(f"ID: {cat.id}, Name: {cat.name}")
