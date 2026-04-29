import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from guard.models import Location, LocationCategory
from cities_light.models import City, Country

# Data provided by the user
hotel_data = {
    "sousse": [
        "Iberostar Selection Diar El Andalous",
        "Iberostar Selection Kantaoui Bay",
        "Marhaba Palace",
        "Royal Kenz Thalasso & Spa",
        "Mövenpick Resort & Marine Spa Sousse",
        "El Mouradi Palace",
        "Seabel Alhambra Beach Golf & Spa",
        "Hotel Riadh Palms"
    ],
    "monastir": [
        "Iberostar Selection Kuriat Palace",
        "Royal Thalassa Monastir",
        "One Resort Aqua Park",
        "Sahara Beach Aquapark Resort",
        "Marina Cap Monastir Appart-Hôtel",
        "Delphin El Habib"
    ],
    "mahdia": [
        "Mahdia Beach & Aqua Park",
        "El Mouradi Mahdia",
        "Thapsus Beach Resort",
        "Club Thapsus",
        "Nour Palace Resort & Thalasso",
        "LTI Mahdia Beach"
    ],
    "sfax": [
        "Borj Dhiafa Hotel",
        "Les Oliviers Palace",
        "Hotel Naher El Founoun",
        "Ibis Sfax"
    ],
    "tunis": [
        "The Residence Tunis",
        "Mövenpick Gammarth",
        "Sheraton Tunis Hotel",
        "Hotel Africa Tunis",
        "Dar El Marsa",
        "Golden Tulip El Mechtel"
    ],
    "kairouan": [
        "Hotel La Kasbah Kairouan",
        "Continental Kairouan",
        "Dar Hassine Allani"
    ],
    "zaghouan": [
        "Dar Zaghouan",
        "Hôtel Source de la Médina Zaghouan"
    ]
}

def populate():
    # 0. Cleanup dummy locations (like "Loc 0", "Loc 1", etc.)
    dummy_count = Location.objects.filter(name__icontains='Loc').delete()[0]
    if dummy_count:
        print(f"Deleted {dummy_count} dummy locations.")

    # 1. Ensure Country Tunisia exists
    try:
        tunisia = Country.objects.get(name='Tunisia')
    except Country.DoesNotExist:
        print("Country Tunisia not found. Please ensure cities_light data is loaded.")
        return

    # 2. Categories dictionary (NEW)
    categories = {
        "hotel": "Hotels",
        "restaurant": "Restaurants",
        "cafe": "Cafes",
        "maison_hote": "Maisons d'hôte"
    }

    # 3. Get or create category objects
    category_objects = {}
    for key, name in categories.items():
        obj, created = LocationCategory.objects.get_or_create(name=name)
        category_objects[key] = obj
        if created:
            print(f"Created category: {name}")

    # 4. Iterate and Create Locations
    for city_name, hotels in hotel_data.items():
        city = City.objects.filter(country=tunisia, name__iexact=city_name).first()

        if not city and city_name == "zaghouan":
            city = City.objects.filter(country=tunisia, name__icontains="Zag").first()
            if not city:
                city = City.objects.create(name="Zaghouan", country=tunisia)
                print(f"Created missing city: {city.name}")

        if not city:
            print(f"City '{city_name}' not found in database. Skipping.")
            continue

        print(f"Processing city: {city.name}")

        for hotel_name in hotels:
            loc, created = Location.objects.update_or_create(
                name=hotel_name,
                city=city,
                defaults={
                    'category': category_objects["hotel"],  # 🔥 هنا التغيير المهم
                    'country': tunisia,
                    'latitude': 0.0,
                    'longitude': 0.0,
                    'name_en': hotel_name,
                    'name_fr': hotel_name,
                    'story_en': f"Description for {hotel_name} in {city.name}.",
                    'story_fr': f"Description pour {hotel_name} à {city.name}.",
                }
            )

            if created:
                print(f"  + Added: {hotel_name}")
            else:
                print(f"  . Updated: {hotel_name}")

if __name__ == "__main__":
    populate()
    print("Population completed.")