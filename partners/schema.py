import strawberry
import strawberry_django
from typing import List, Optional
from strawberry import auto
from core.exceptions import DomainException
from .models import Partner
from .services import PartnerService, LocationService
from guard.models import Location, LocationCategory
from cities_light.models import City, Country

# --- Types ---

@strawberry.type
class ErrorType:
    code: str
    message: str

@strawberry_django.type(Partner)
class PartnerType:
    id: strawberry.ID
    company_name: auto
    email: auto
    phone: auto
    website: auto
    status: auto
    created_at: auto

    @strawberry.field
    def locations(self, root) -> List[strawberry.LazyType["LocationType", "api.schema"]]:
        return root.owned_locations.all()

@strawberry.type
class PartnerPayload:
    partner: Optional[PartnerType] = None
    success: bool = True
    errors: Optional[List[ErrorType]] = None

@strawberry.type
class LocationPayload:
    location: Optional[strawberry.LazyType["LocationType", "api.schema"]] = None
    success: bool = True
    errors: Optional[List[ErrorType]] = None

# --- Inputs ---

@strawberry.input
class CreatePartnerInput:
    name: str # company_name
    email: str
    password: str
    phone: Optional[str] = ""
    website: Optional[str] = ""

@strawberry.input
class UpdatePartnerInput:
    name: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None

@strawberry.input
class AddLocationInput:
    name: str
    city_id: Optional[int] = None
    country_id: Optional[int] = None
    category_id: Optional[int] = None
    latitude: Optional[float] = 0.0
    longitude: Optional[float] = 0.0

# --- Mutations ---

@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_partner(self, input: CreatePartnerInput) -> PartnerPayload:
        try:
            partner = PartnerService.create_partner(
                email=input.email,
                password=input.password,
                company_name=input.name,
                phone=input.phone
            )
            # Website field isn't in create_partner service yet, let's update it
            if input.website:
                partner.website = input.website
                partner.save()
            return PartnerPayload(partner=partner)
        except DomainException as e:
            return PartnerPayload(
                success=False,
                errors=[ErrorType(code=e.code, message=str(e))]
            )

    @strawberry.mutation
    def add_location_to_partner(self, partner_id: strawberry.ID, input: AddLocationInput) -> LocationPayload:
        try:
            location = LocationService.add_location_to_partner(
                partner_id=partner_id,
                name=input.name,
                city_id=input.city_id,
                country_id=input.country_id,
                category_id=input.category_id,
                latitude=input.latitude,
                longitude=input.longitude
            )
            return LocationPayload(location=location) 
        except DomainException as e:
            from api.schema import LocationType # Needed for type hint in return
            return LocationPayload(
                success=False,
                errors=[ErrorType(code=e.code, message=str(e))]
            )

    @strawberry.mutation
    def update_partner(self, id: strawberry.ID, input: UpdatePartnerInput) -> PartnerPayload:
        try:
            partner = Partner.objects.get(id=id)
            if input.name: partner.company_name = input.name
            if input.phone: partner.phone = input.phone
            if input.website: partner.website = input.website
            partner.save()
            return PartnerPayload(partner=partner)
        except Partner.DoesNotExist:
            return PartnerPayload(
                success=False,
                errors=[ErrorType(code="NOT_FOUND", message="Partenaire introuvable.")]
            )

# --- Query ---

@strawberry.type
class Query:
    @strawberry.field
    def partners(self, status: Optional[str] = None, search: Optional[str] = None) -> List[PartnerType]:
        queryset = Partner.objects.all()
        if status:
            queryset = queryset.filter(status=status)
        if search:
            queryset = queryset.filter(company_name__icontains=search) | queryset.filter(email__icontains=search)
        return queryset
