from django.db import transaction
from django.conf import settings
from django.utils import timezone
from core.exceptions import DomainException
from guard.models import GuardUser, Location
from guard.services import EmailVerificationService
from .models import Partner

class PartnerService:
    @staticmethod
    @transaction.atomic
    def create_partner(email, password, company_name, phone=""):
        # 1. Vérifier si l'utilisateur existe déjà
        if GuardUser.objects.filter(email=email).exists():
            raise DomainException("Cet email est déjà utilisé.", code="CONFLICT")

        # 2. Créer l'utilisateur (on le met is_verified=False)
        user = GuardUser.objects.create_user(
            email=email,
            password=password,
            is_verified=False
        )

        # 3. Créer le profil Partner
        partner = Partner.objects.create(
            user=user,
            company_name=company_name,
            email=email,
            phone=phone,
            status='pending'
        )

        # 4. Générer le token de vérification
        raw_token = EmailVerificationService.issue_verification_token(user)

        # 5. Envoyer l'email (via Celery)
        from guard.tasks import send_verification_email_task
        send_verification_email_task.delay(user.id, raw_token)

        return partner

class LocationService:
    @staticmethod
    def add_location_to_partner(partner_id, name, city_id=None, country_id=None, category_id=None, latitude=0, longitude=0):
        try:
            partner = Partner.objects.get(id=partner_id)
        except Partner.DoesNotExist:
            raise DomainException("Partenaire introuvable.", code="NOT_FOUND")

        location = Location.objects.create(
            partner=partner,
            name=name,
            city_id=city_id,
            country_id=country_id,
            category_id=category_id,
            latitude=latitude,
            longitude=longitude,
            story="" # Par défaut vide
        )
        return location
