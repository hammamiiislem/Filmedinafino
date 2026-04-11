"""
Push notification service for sending FCM notifications
when new locations, events, or hikings are created.
"""
import logging
from typing import List, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    from firebase_admin import messaging
    from fcm_django.models import FCMDevice
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logger.warning("firebase_admin or fcm_django not available. Push notifications will be disabled.")


class NotificationService:
    """Service for sending push notifications via FCM"""

    @staticmethod
    def get_all_active_devices() -> List[FCMDevice]:
        """Get all active FCM devices for sending notifications"""
        if not FIREBASE_AVAILABLE:
            return []
        return FCMDevice.objects.filter(active=True)

    @staticmethod
    def get_user_tokens(devices: List[FCMDevice] = None) -> List[str]:
        """Extract registration tokens from FCM devices"""
        if not FIREBASE_AVAILABLE:
            return []
        if devices is None:
            devices = NotificationService.get_all_active_devices()
        return [device.registration_id for device in devices if device.registration_id]

    @staticmethod
    def build_absolute_image_url(image_field) -> Optional[str]:
        """Build absolute URL for an image field"""
        if not image_field:
            return None
        try:
            # In Django, request is not available in signals context
            # We'll build URL using settings
            if not image_field.name:
                return None
                
            base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')
            media_url = settings.MEDIA_URL.lstrip('/')
            
            # Build full URL
            return f"{base_url}/{media_url}{image_field.name}"
        except Exception as e:
            logger.error(f"Error building image URL: {e}")
            return None

    @staticmethod
    def send_new_event_notification(event) -> Optional[messaging.BatchResponse]:
        """Send notification when a new event is added"""
        if not FIREBASE_AVAILABLE:
            logger.warning("Firebase not available, skipping notification")
            return None

        try:
            # Get all active device tokens
            tokens = NotificationService.get_user_tokens()
            if not tokens:
                logger.info("No active FCM devices found, skipping notification")
                return None

            # Get first image URL if available
            image_url = None
            first_image = event.images.first()
            if first_image and first_image.image:
                image_url = NotificationService.build_absolute_image_url(first_image.image)

            # Format event date
            start_date_str = event.startDate.strftime("%B %d, %Y") if event.startDate else ""

            # Build notification message
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title='🎉 New Event Coming Up!',
                    body=f'{event.name} - {start_date_str}',
                    image=image_url,
                ),
                data={
                    'type': 'new_event',
                    'screen': 'event_detail',
                    'id': str(event.id),
                    'event_id': str(event.id),
                    'location_id': str(event.location.id) if event.location else '',
                    'city_id': str(event.city.id) if event.city else '',
                    'click_action': 'OPEN_EVENT',
                    'link': f"/events/{event.id}",
                },
                tokens=tokens,
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            badge=1,
                            mutable_content=True,
                            content_available=True,
                            alert=messaging.ApsAlert(
                                title='🎉 New Event Coming Up!',
                                body=f'{event.name} - {start_date_str}',
                            ),
                        )
                    )
                ),
                android=messaging.AndroidConfig(
                    notification=messaging.AndroidNotification(
                        sound='default',
                        channel_id='events',
                        priority='high',
                        click_action='OPEN_EVENT',
                    )
                ),
            )

            # Send notification
            response = messaging.send_multicast(message)
            logger.info(
                f"Event notification sent: {response.success_count} successful, "
                f"{response.failure_count} failed for event {event.id}"
            )
            return response

        except Exception as e:
            logger.error(f"Error sending event notification: {e}", exc_info=True)
            return None

    @staticmethod
    def send_new_location_notification(location) -> Optional[messaging.BatchResponse]:
        """Send notification when a new location is added"""
        if not FIREBASE_AVAILABLE:
            logger.warning("Firebase not available, skipping notification")
            return None

        try:
            # Get all active device tokens
            tokens = NotificationService.get_user_tokens()
            if not tokens:
                logger.info("No active FCM devices found, skipping notification")
                return None

            # Get first image URL if available
            image_url = None
            first_image = location.images.first()
            if first_image and first_image.image:
                image_url = NotificationService.build_absolute_image_url(first_image.image)

            # Build notification message
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title='📍 New Place to Explore!',
                    body=f'Check out: {location.name}',
                    image=image_url,
                ),
                data={
                    'type': 'new_location',
                    'screen': 'location_detail',
                    'id': str(location.id),
                    'location_id': str(location.id),
                    'category_id': str(location.category.id) if location.category else '',
                    'city_id': str(location.city.id) if location.city else '',
                    'click_action': 'OPEN_LOCATION',
                    'link': f"/locations/{location.id}",
                },
                tokens=tokens,
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            badge=1,
                            mutable_content=True,
                            content_available=True,
                            alert=messaging.ApsAlert(
                                title='📍 New Place to Explore!',
                                body=f'Check out: {location.name}',
                            ),
                        )
                    )
                ),
                android=messaging.AndroidConfig(
                    notification=messaging.AndroidNotification(
                        sound='default',
                        channel_id='locations',
                        priority='high',
                        click_action='OPEN_LOCATION',
                    )
                ),
            )

            # Send notification
            response = messaging.send_multicast(message)
            logger.info(
                f"Location notification sent: {response.success_count} successful, "
                f"{response.failure_count} failed for location {location.id}"
            )
            return response

        except Exception as e:
            logger.error(f"Error sending location notification: {e}", exc_info=True)
            return None

    @staticmethod
    def send_new_hiking_notification(hiking) -> Optional[messaging.BatchResponse]:
        """Send notification when a new hiking trail is added"""
        if not FIREBASE_AVAILABLE:
            logger.warning("Firebase not available, skipping notification")
            return None

        try:
            # Get all active device tokens
            tokens = NotificationService.get_user_tokens()
            if not tokens:
                logger.info("No active FCM devices found, skipping notification")
                return None

            # Get first image URL if available
            image_url = None
            first_image = hiking.images.first()
            if first_image and first_image.image:
                image_url = NotificationService.build_absolute_image_url(first_image.image)

            # Build notification message
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title='🥾 New Hiking Trail!',
                    body=f'Explore: {hiking.name}',
                    image=image_url,
                ),
                data={
                    'type': 'new_hiking',
                    'screen': 'hiking_detail',
                    'id': str(hiking.id),
                    'hiking_id': str(hiking.id),
                    'city_id': str(hiking.city.id) if hiking.city else '',
                    'click_action': 'OPEN_HIKING',
                    'link': f"/hikings/{hiking.id}",
                },
                tokens=tokens,
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            badge=1,
                            mutable_content=True,
                            content_available=True,
                            alert=messaging.ApsAlert(
                                title='🥾 New Hiking Trail!',
                                body=f'Explore: {hiking.name}',
                            ),
                        )
                    )
                ),
                android=messaging.AndroidConfig(
                    notification=messaging.AndroidNotification(
                        sound='default',
                        channel_id='hikings',
                        priority='high',
                        click_action='OPEN_HIKING',
                    )
                ),
            )

            # Send notification
            response = messaging.send_multicast(message)
            logger.info(
                f"Hiking notification sent: {response.success_count} successful, "
                f"{response.failure_count} failed for hiking {hiking.id}"
            )
            return response

        except Exception as e:
            logger.error(f"Error sending hiking notification: {e}", exc_info=True)
            return None
