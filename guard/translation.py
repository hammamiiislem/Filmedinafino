from modeltranslation.translator import register, TranslationOptions
from .models import (
    Location,
    LocationCategory,
    Event,
    EventCategory,
    Tip,
    Hiking,
    PublicTransportType,
    PublicTransport,
)


@register(PublicTransportType)
class PublicTransportTypeTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(Location)
class LocationTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "story",
    )


@register(LocationCategory)
class LocationCategoryTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Event)
class EventTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "description",
    )


@register(EventCategory)
class EventCategoryTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Tip)
class TipTranslationOptions(TranslationOptions):
    fields = ("description",)


@register(Hiking)
class HikingTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "description",
    )


#@register(PublicTransportType)
#class PublicTransportTypeTranslationOptions(TranslationOptions):
    #fields = ("name",)
