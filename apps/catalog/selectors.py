"""Read-side queries of the catalog."""

from dataclasses import dataclass
from decimal import Decimal

from django.conf import settings
from django.contrib.postgres.search import TrigramSimilarity, TrigramWordSimilarity
from django.db.models import (
    Case,
    CharField,
    F,
    IntegerField,
    Max,
    Min,
    Prefetch,
    Q,
    QuerySet,
    Value,
    When,
)
from django.db.models.functions import Coalesce, Greatest, NullIf
from django.utils import translation

from apps.catalog.alphabet import sort_letters
from apps.catalog.models import (
    BerryColor,
    Dictionary,
    GrowthVigor,
    PulpConsistency,
    RipeningPeriod,
    Taste,
    Variety,
    VarietyPhoto,
)

# Minimal word similarity for a fuzzy (typo-tolerant) search match.
SEARCH_SIMILARITY_THRESHOLD = 0.4

DICTIONARY_MODELS: dict[str, type[Dictionary]] = {
    "ripening": RipeningPeriod,
    "berry_color": BerryColor,
    "pulp": PulpConsistency,
    "taste": Taste,
    "vigor": GrowthVigor,
}

# Filter name -> (lower bound field, upper bound field) of the variety.
RANGE_FIELDS: dict[str, tuple[str, str]] = {
    "bunch_weight": ("bunch_weight_min", "bunch_weight_max"),
    "berry_weight": ("berry_weight_min", "berry_weight_max"),
    "berry_size": ("berry_size_min", "berry_size_max"),
    "disease": ("disease_susceptibility_min", "disease_susceptibility_max"),
    "frost": ("frost_resistance", "frost_resistance"),
}


def _language_codes() -> list[str]:
    return [code for code, _name in settings.LANGUAGES]


def current_language() -> str:
    """Active language if it is a site language, otherwise the default one."""
    language = translation.get_language() or settings.LANGUAGE_CODE
    return language if language in _language_codes() else settings.LANGUAGE_CODE


def localized(field: str, language: str | None = None) -> Coalesce:
    """Expression for a translated field in `language`, falling back to the default language."""
    language = language or current_language()
    default = F(f"{field}_{settings.LANGUAGE_CODE}")
    if language == settings.LANGUAGE_CODE:
        return Coalesce(default, Value(""), output_field=CharField())
    return Coalesce(
        NullIf(F(f"{field}_{language}"), Value("")),
        default,
        Value(""),
        output_field=CharField(),
    )


def published_varieties() -> QuerySet[Variety]:
    return Variety.objects.filter(is_published=True)


def card_photos_prefetch() -> Prefetch:
    """Photos ordered so that the main one comes first (`variety.card_photos[0]`)."""
    return Prefetch(
        "photos",
        queryset=VarietyPhoto.objects.order_by("-is_main", "order", "pk"),
        to_attr="card_photos",
    )


def variety_list() -> QuerySet[Variety]:
    """Published varieties with everything a catalog card needs, in a constant number of queries."""
    return (
        published_varieties()
        .select_related("ripening", "berry_color")
        .prefetch_related(card_photos_prefetch())
        .annotate(display_name=localized("name"))
    )


def variety_detail_queryset() -> QuerySet[Variety]:
    """Published varieties with all relations of the variety page."""
    return (
        published_varieties()
        .select_related(*DICTIONARY_MODELS)
        .prefetch_related("photos", "videos")
    )


def search_varieties(queryset: QuerySet[Variety], query: str) -> QuerySet[Variety]:
    """
    Find varieties by name or alternative names in any site language.

    Substring matches ignore case and accents; fuzzy trigram matches catch typos and
    Russian spellings. Results are annotated with `search_rank` (how well the query matches
    some word of a name) and `search_closeness` (how close the whole name is to the query),
    and ordered by them, so that `Перлина` comes before `Перлина Саби`.
    """
    query = query.strip()
    if not query:
        return queryset
    fields = [f"{field}_{code}" for field in ("name", "alt_names") for code in _language_codes()]
    condition = Q()
    for field in fields:
        condition |= Q(**{f"{field}__unaccent__icontains": query})
    values = [Coalesce(F(field), Value("")) for field in fields]
    return (
        queryset.annotate(
            search_rank=Greatest(*(TrigramWordSimilarity(query, value) for value in values)),
            search_closeness=Greatest(*(TrigramSimilarity(value, query) for value in values)),
        )
        .filter(condition | Q(search_rank__gte=SEARCH_SIMILARITY_THRESHOLD))
        .order_by("-search_rank", "-search_closeness", "pk")
    )


def filter_range_overlap(
    queryset: QuerySet[Variety],
    name: str,
    low: Decimal | int | None,
    high: Decimal | int | None,
) -> QuerySet[Variety]:
    """
    Keep varieties whose range of a characteristic intersects `[low, high]`.

    A variety with only one bound uses it for both ends; varieties with no value are excluded
    as soon as any bound of the filter is given.
    """
    min_field, max_field = RANGE_FIELDS[name]
    if low is not None:
        queryset = queryset.filter(
            Q(**{f"{max_field}__gte": low})
            | Q(**{f"{max_field}__isnull": True, f"{min_field}__gte": low})
        )
    if high is not None:
        queryset = queryset.filter(
            Q(**{f"{min_field}__lte": high})
            | Q(**{f"{min_field}__isnull": True, f"{max_field}__lte": high})
        )
    return queryset


def similar_varieties(variety: Variety, limit: int = 4) -> list[Variety]:
    """
    Published varieties that share the most characteristics with `variety`.

    Ripening period weighs most, then berry colour and taste; ties go to the more popular ones.
    """
    weights = {"ripening": 3, "berry_color": 2, "taste": 1}
    score = sum(
        (
            Case(
                When(**{f"{field}_id": getattr(variety, f"{field}_id")}, then=Value(weight)),
                default=Value(0),
                output_field=IntegerField(),
            )
            for field, weight in weights.items()
            if getattr(variety, f"{field}_id") is not None
        ),
        start=Value(0, output_field=IntegerField()),
    )
    return list(
        variety_list()
        .exclude(pk=variety.pk)
        .annotate(similarity=score)
        .filter(similarity__gt=0)
        .order_by("-similarity", "-views_count", "pk")[:limit]
    )


@dataclass(frozen=True)
class NumberRange:
    min: Decimal | int | None
    max: Decimal | int | None


def filter_options() -> dict[str, object]:
    """Reference-list values and characteristic bounds for building the filter form."""
    varieties = published_varieties()
    aggregates = varieties.aggregate(
        **{
            f"{name}_{bound}": aggregate(field)
            for name, (min_field, max_field) in RANGE_FIELDS.items()
            for bound, aggregate, field in (("min", Min, min_field), ("max", Max, max_field))
        }
    )
    ranges = {
        name: NumberRange(min=aggregates[f"{name}_min"], max=aggregates[f"{name}_max"])
        for name in RANGE_FIELDS
    }
    dictionaries = {name: list(model.objects.all()) for name, model in DICTIONARY_MODELS.items()}
    return {**dictionaries, "ranges": ranges}


def available_letters(language: str | None = None) -> list[str]:
    """Letters (in alphabet order) that start at least one published variety name in `language`."""
    language = language or current_language()
    field = f"first_letter_{language}"
    letters = published_varieties().order_by().values_list(field, flat=True).distinct()
    return sort_letters(letters, language)


def random_photos(limit: int) -> QuerySet[VarietyPhoto]:
    """Random photos of published varieties (footer gallery)."""
    return (
        VarietyPhoto.objects.filter(variety__is_published=True)
        .select_related("variety")
        .order_by("?")[:limit]
    )
