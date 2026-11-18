"""factory-boy factories of the catalog (also used by the demo data command)."""

import factory
from factory.django import DjangoModelFactory, ImageField

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


class DictionaryFactory(DjangoModelFactory):
    name_uk = factory.Sequence(lambda n: f"Значення {n}")
    name_en = factory.Sequence(lambda n: f"Value {n}")
    order = factory.Sequence(lambda n: n)

    class Meta:
        abstract = True


class RipeningPeriodFactory(DictionaryFactory):
    class Meta:
        model = RipeningPeriod


class BerryColorFactory(DictionaryFactory):
    class Meta:
        model = BerryColor


class PulpConsistencyFactory(DictionaryFactory):
    class Meta:
        model = PulpConsistency


class TasteFactory(DictionaryFactory):
    class Meta:
        model = Taste


class GrowthVigorFactory(DictionaryFactory):
    class Meta:
        model = GrowthVigor


class VarietyFactory(DjangoModelFactory):
    name_uk = factory.Sequence(lambda n: f"Сорт {n}")
    name_en = factory.Sequence(lambda n: f"Variety {n}")
    is_published = True

    class Meta:
        model = Variety


class VarietyPhotoFactory(DjangoModelFactory):
    variety = factory.SubFactory(VarietyFactory)
    image = ImageField(width=40, height=30, color="purple", format="JPEG")
    order = factory.Sequence(lambda n: n)

    class Meta:
        model = VarietyPhoto


class VarietyVideoFactory(DjangoModelFactory):
    variety = factory.SubFactory(VarietyFactory)
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    title_uk = "Огляд сорту"
    title_en = "Variety review"

    class Meta:
        model = VarietyVideo
