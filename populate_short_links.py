import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from guard.models import Event, Ad
from shared.short_io import ShortIOService

def populate_short_links():
    service = ShortIOService()
    
    # 1. Populate Events
    events_to_fix = Event.objects.filter(short_id__isnull=True)
    print(f"Fixing {events_to_fix.count()} events...")
    for event in events_to_fix:
        print(f" - Processing event: {event.name}")
        short_data = service.shorten_url(event.link, title=f"Event: {event.name}")
        if short_data:
            event.short_link = short_data.get("secureShortURL") or short_data.get("shortURL")
            event.short_id = short_data.get("idString")
            event.save()
            print(f"   Done: {event.short_link}")
        else:
            print(f"   Failed to shorten URL for {event.name}")

    # 2. Populate Ads
    ads_to_fix = Ad.objects.filter(short_id__isnull=True, is_active=True)
    print(f"Fixing {ads_to_fix.count()} ads...")
    for ad in ads_to_fix:
        print(f" - Processing ad: {ad.name}")
        short_data = service.shorten_url(ad.link, title=f"Ad: {ad.name}")
        if short_data:
            ad.short_link = short_data.get("secureShortURL") or short_data.get("shortURL")
            ad.short_id = short_data.get("idString")
            ad.save()
            print(f"   Done: {ad.short_link}")
        else:
            print(f"   Failed to shorten URL for {ad.name}")

if __name__ == "__main__":
    populate_short_links()
