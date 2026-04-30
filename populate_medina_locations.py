import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from guard.models import Location, LocationCategory
from cities_light.models import City, Country

data = {
    "sousse": {
        "Restaurant": ["Restaurant Café Seles", "Restaurant du Peuple", "Dar Riani"],
        "Cafe": ["Café El Medina", "Café Sidi Boujaafar (قريب للمدينة)", "Café Kasbah"],
        "Hotel": ["Dar Baaziz", "Dar Antonia", "Dar Lekbira"]
    },
    "kairouan": {
        "Restaurant": ["Restaurant El Brija", "Restaurant Sabra", "Restaurant Ennakhil"],
        "Cafe": ["Café El Kasbah", "Café Jamaa", "Café Ennakhil"],
        "Hotel": ["Dar Hassine Allani", "Dar Alouini", "Maison d’hôte La Kasbah"]
    },
    "mahdia": {
        "Restaurant": ["Restaurant Neptune", "Restaurant El Médina", "Restaurant Sidi Salem"],
        "Cafe": ["Café El Médina", "Café Borj Erras", "Café Sidi Salem"],
        "Hotel": ["Dar Evelyne", "Dar Jamila", "Hôtel Dar El Amen"]
    },
    "monastir": {
        "Restaurant": ["Restaurant Marina", "Restaurant Le Pirate", "Restaurant Le Roi"],
        "Cafe": ["Café Médina", "Café Marina", "Café Ribat"],
        "Hotel": ["Dar Benti", "Hôtel Regency", "Maison d’hôte Ribat"]
    },
    "zaghouan": {
        "Restaurant": ["Restaurant El Médina", "Restaurant Ain Zaghouan"],
        "Cafe": ["Café El Médina", "Café Ennakhil"],
        "Hotel": ["Dar Zaghouan", "Maison d’hôte Dar Othman"]
    },
    "tunis": {
        "Restaurant": ["Dar El Jeld", "Fondouk El Attarine", "Restaurant Essaraya"],
        "Cafe": ["Café Mrabet", "Café El M’rabet", "Café Diwan"],
        "Hotel": ["Dar Ben Gacem", "Dar El Medina", "Maison d’hôte Dar Ya"]
    }
}

def populate():
    try:
        tunisia = Country.objects.get(name='Tunisia')
    except Country.DoesNotExist:
        print("Country Tunisia not found.")
        return

    # Ensure categories exist
    cat_restaurant, _ = LocationCategory.objects.get_or_create(name="Restaurant")
    cat_cafe, _ = LocationCategory.objects.get_or_create(name="Cafe")
    cat_hotel, _ = LocationCategory.objects.get_or_create(name="Hotel")

    cat_map = {
        "Restaurant": cat_restaurant,
        "Cafe": cat_cafe,
        "Hotel": cat_hotel
    }

    for city_name, categories_data in data.items():
        city = City.objects.filter(country=tunisia, name__iexact=city_name).first()
        if not city:
            city = City.objects.filter(country=tunisia, name__icontains=city_name).first()

        if not city:
            print(f"City '{city_name}' not found. Creating it.")
            city = City.objects.create(name=city_name.capitalize(), country=tunisia)

        print(f"Processing city: {city.name}")

        for cat_name, places in categories_data.items():
            category = cat_map[cat_name]
            for place_name in places:
                loc, created = Location.objects.update_or_create(
                    name=place_name,
                    city=city,
                    defaults={
                        'category': category,
                        'country': tunisia,
                        'latitude': 0.0,
                        'longitude': 0.0,
                        'name_en': place_name,
                        'name_fr': place_name,
                        'story_en': f"{place_name} in the medina of {city.name}.",
                        'story_fr': f"{place_name} dans la médina de {city.name}.",
                    }
                )
                if created:
                    print(f"  + Added: {place_name} ({cat_name})")
                else:
                    print(f"  . Updated: {place_name} ({cat_name})")

if __name__ == "__main__":
    populate()
    print("Population completed.")
