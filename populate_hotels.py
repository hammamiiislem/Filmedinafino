import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from guard.models import Location, LocationCategory
from cities_light.models import City, Country

# Data provided by the user
hotel_data = {
  "kairouan": [
    "Hotel La Kasbah",
    "Hotel Continental",
    "Tunisia Hotel",
    "Amina Hotel",
    "Hotel Sabra"
  ],
  "mahdia": [
    "Mahdia Palace Thalasso",
    "Iberostar Royal El Mansour",
    "El Mouradi Mahdia",
    "Thalassa Mahdia"
  ],
  "monastir": [
    "Royal Thalassa Monastir",
    "El Mouradi Skanes",
    "Helya Beach Hotel",
    "Skanes Serail"
  ],
  "sfax": [
    "Les Oliviers Palace",
    "Ibis Sfax",
    "Business Hotel Sfax",
    "Hotel Syphax"
  ],
  "sousse": [
    "Movenpick Resort & Marine Spa Sousse",
    "El Mouradi Palace",
    "Marhaba Palace",
    "Sousse Palace Hotel & Spa"
  ],
  "tunis": [
    "Laico Tunis",
    "Sheraton Tunis Hotel",
    "Movenpick Hotel du Lac Tunis",
    "Golden Tulip El Mechtel"
  ]
}

def populate():
    # 1. Ensure Country Tunisia exists
    try:
        tunisia = Country.objects.get(name='Tunisia')
    except Country.DoesNotExist:
        print("Country Tunisia not found. Please ensure cities_light data is loaded.")
        return

    # 2. Get or Create Category "Hotels"
    hotel_category, created = LocationCategory.objects.get_or_create(name="Hotels")
    if created:
        print(f"Created category: {hotel_category.name}")

    # 3. Iterate and Create Locations
    for city_name, hotels in hotel_data.items():
        city = City.objects.filter(country=tunisia, name__iexact=city_name).first()
        if not city:
            print(f"City '{city_name}' not found in database. Skipping.")
            continue
        
        print(f"Processing city: {city.name}")
        for hotel_name in hotels:
            # Avoid duplicates by name and city
            loc, created = Location.objects.get_or_create(
                name=hotel_name,
                city=city,
                defaults={
                    'category': hotel_category,
                    'country': tunisia,
                    'latitude': 0.0,
                    'longitude': 0.0,
                    'story': f"Description for {hotel_name} in {city.name}.",
                    'story_en': f"Description for {hotel_name} in {city.name}.",
                    'story_fr': f"Description pour {hotel_name} à {city.name}.",
                }
            )
            if created:
                print(f"  + Added: {hotel_name}")
            else:
                # Update category if it was different
                if loc.category != hotel_category:
                    loc.category = hotel_category
                    loc.save()
                    print(f"  * Updated category for: {hotel_name}")
                else:
                    print(f"  . Already exists: {hotel_name}")

if __name__ == "__main__":
    populate()
    print("Population completed.")
