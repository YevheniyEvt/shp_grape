"""django-modeltranslation registration of the catalog models."""

from modeltranslation.translator import TranslationOptions, register

from apps.catalog.models import (
    BerryColor,
    GrowthVigor,
    PulpConsistency,
    RipeningPeriod,
    Taste,
    Variety,
    VarietyPhoto,
    VarietyVideo,
)


@register([RipeningPeriod, BerryColor, PulpConsistency, Taste, GrowthVigor])
class DictionaryTranslationOptions(TranslationOptions):
    fields = ("name",)
    required_languages = ("uk",)


@register(Variety)
class VarietyTranslationOptions(TranslationOptions):
    fields = ("name", "alt_names", "author", "description", "first_letter")
    required_languages = {"uk": ("name",)}


@register(VarietyPhoto)
class VarietyPhotoTranslationOptions(TranslationOptions):
    fields = ("alt",)


@register(VarietyVideo)
class VarietyVideoTranslationOptions(TranslationOptions):
    fields = ("title",)
