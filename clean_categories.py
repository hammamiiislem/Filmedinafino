import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from guard.models import Event, EventCategory

target_names = ["Festival", "Sport", "Culture", "Excursion", "Randonnée"]

def clean_categories():
    print("--- Cleaning Event Categories ---")
    
    # 1. Create/Ensure target categories exist
    targets = {}
    for name in target_names:
        # Create with proper Case
        cat, created = EventCategory.objects.get_or_create(name=name)
        targets[name.lower()] = cat
        if created:
            print(f"Created category: {name}")

    # 2. Handle existing categories
    all_cats = EventCategory.objects.all()
    for cat in all_cats:
        name_lower = cat.name.lower()
        # Normalization for matching (e.g. randonne -> randonnée)
        norm_name = name_lower.replace("é", "e").replace("è", "e").replace("ê", "e")
        
        match = None
        if name_lower in targets:
            match = targets[name_lower]
        elif "randonne" in norm_name:
            match = targets["randonnée"]
        elif "festiv" in norm_name:
            match = targets["festival"]
        elif "sport" in norm_name:
            match = targets["sport"]
        elif "cultur" in norm_name:
            match = targets["culture"]
        elif "excurs" in norm_name:
            match = targets["excursion"]

        if match:
            if cat.id != match.id:
                print(f"Merging '{cat.name}' (ID: {cat.id}) into '{match.name}'")
                Event.objects.filter(category=cat).update(category=match)
                cat.delete()
        else:
            # If it's not in targets and doesn't match roughly, reassign events to 'Culture' and delete
            if cat.name not in target_names:
                count = Event.objects.filter(category=cat).count()
                print(f"Removing unused or extra category '{cat.name}' (Events count: {count})")
                if count > 0:
                    Event.objects.filter(category=cat).update(category=targets["culture"])
                cat.delete()

    print("--- Cleanup Done ---")
    final_cats = EventCategory.objects.all().values_list('name', flat=True)
    print(f"Final categories: {list(final_cats)}")

if __name__ == "__main__":
    clean_categories()
