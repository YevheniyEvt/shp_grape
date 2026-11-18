"""Query-string filters of the variety list (django-filter)."""

from django.db.models import F, Q, QuerySet
from django.utils.translation import gettext_lazy as _
from django_filters import rest_framework as filters
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field

from apps.catalog import selectors
from apps.catalog.alphabet import DIGITS_GROUP
from apps.catalog.models import (
    BerryColor,
    GrowthVigor,
    PulpConsistency,
    RipeningPeriod,
    Taste,
    Variety,
)

ORDERING_CHOICES = [
    ("name", _("name")),
    ("ripening", _("ripening period")),
    ("-created", _("newest first")),
    ("-views_count", _("most viewed first")),
]


@extend_schema_field(OpenApiTypes.STR)
class SlugMultipleChoiceFilter(filters.ModelMultipleChoiceFilter):
    """Reference-list filter by slugs (`?ripening=early&ripening=mid`)."""


def _dictionary_filter(field: str, model, label) -> SlugMultipleChoiceFilter:
    return SlugMultipleChoiceFilter(
        field_name=f"{field}__slug",
        queryset=model.objects.all(),
        to_field_name="slug",
        label=label,
        help_text=_("Slug; repeat the parameter to select several values."),
    )


class RangeBoundFilter(filters.NumberFilter):
    """One bound of a characteristic range; matches varieties whose range intersects the filter."""

    def __init__(self, range_name: str, bound: str, **kwargs) -> None:
        self.range_name = range_name
        self.bound = bound
        super().__init__(**kwargs)

    def filter(self, qs: QuerySet, value):
        if value is None:
            return qs
        low, high = (value, None) if self.bound == "min" else (None, value)
        return selectors.filter_range_overlap(qs, self.range_name, low, high)


class VarietyFilter(filters.FilterSet):
    letter = filters.CharFilter(
        method="filter_letter",
        label=_("first letter"),
        help_text=_("A letter of the current language's alphabet or `#` for names with digits."),
    )
    search = filters.CharFilter(method="filter_search", label=_("search"))
    ripening = _dictionary_filter("ripening", RipeningPeriod, _("ripening period"))
    berry_color = _dictionary_filter("berry_color", BerryColor, _("berry colour"))
    pulp = _dictionary_filter("pulp", PulpConsistency, _("pulp consistency"))
    taste = _dictionary_filter("taste", Taste, _("taste"))
    vigor = _dictionary_filter("vigor", GrowthVigor, _("growth vigour"))
    bunch_weight_min = RangeBoundFilter("bunch_weight", "min", label=_("bunch weight from"))
    bunch_weight_max = RangeBoundFilter("bunch_weight", "max", label=_("bunch weight to"))
    berry_weight_min = RangeBoundFilter("berry_weight", "min", label=_("berry weight from"))
    berry_weight_max = RangeBoundFilter("berry_weight", "max", label=_("berry weight to"))
    berry_size_min = RangeBoundFilter("berry_size", "min", label=_("berry size from"))
    berry_size_max = RangeBoundFilter("berry_size", "max", label=_("berry size to"))
    disease_min = RangeBoundFilter("disease", "min", label=_("disease susceptibility from"))
    disease_max = RangeBoundFilter("disease", "max", label=_("disease susceptibility to"))
    frost_min = RangeBoundFilter("frost", "min", label=_("frost resistance from"))
    frost_max = RangeBoundFilter("frost", "max", label=_("frost resistance to"))
    in_stock = filters.BooleanFilter(method="filter_in_stock", label=_("in stock"))
    featured = filters.BooleanFilter(field_name="is_featured", label=_("featured"))
    ordering = filters.ChoiceFilter(
        choices=ORDERING_CHOICES, method="filter_ordering", label=_("ordering")
    )

    class Meta:
        model = Variety
        fields: list[str] = []

    @property
    def qs(self) -> QuerySet[Variety]:
        queryset = super().qs
        # Without an explicit ordering: best search matches first, otherwise alphabetical.
        # (modeltranslation turns Meta.ordering into an explicit `order_by`, so check the form.)
        data = self.form.cleaned_data
        if not data.get("ordering") and not data.get("search", "").strip():
            queryset = queryset.order_by("display_name", "pk")
        return queryset

    def filter_letter(self, queryset: QuerySet, _name: str, value: str) -> QuerySet:
        letter = value[:1].upper()  # the form field already strips whitespace
        field = f"first_letter_{selectors.current_language()}"
        return queryset.filter(**{field: DIGITS_GROUP if letter.isdigit() else letter})

    def filter_search(self, queryset: QuerySet, _name: str, value: str) -> QuerySet:
        return selectors.search_varieties(queryset, value)

    def filter_in_stock(self, queryset: QuerySet, _name: str, value: bool | None) -> QuerySet:
        in_stock = Q(cutting_available=True) | Q(sapling_available=True)
        return queryset.filter(in_stock) if value else queryset.exclude(in_stock)

    def filter_ordering(self, queryset: QuerySet, _name: str, value: str) -> QuerySet:
        orderings = {
            "name": ["display_name", "pk"],
            "ripening": [F("ripening__order").asc(nulls_last=True), "display_name", "pk"],
            "-created": ["-created_at", "-pk"],
            "-views_count": ["-views_count", "display_name", "pk"],
        }
        return queryset.order_by(*orderings[value])
