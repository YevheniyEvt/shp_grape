from decimal import Decimal

import pytest
from django.utils import translation

from apps.catalog import selectors
from apps.catalog.models import RipeningPeriod, Variety
from apps.catalog.tests.factories import (
    BerryColorFactory,
    RipeningPeriodFactory,
    TasteFactory,
    VarietyFactory,
    VarietyPhotoFactory,
)

pytestmark = pytest.mark.django_db


def names(queryset) -> list[str]:
    return [variety.name_uk for variety in queryset]


class TestSearch:
    @pytest.fixture
    def varieties(self):
        return [
            VarietyFactory(name_uk="Ранній Зоряний", name_en="Early Starry"),
            VarietyFactory(name_uk="Ювілейний", name_en="Jubilee", alt_names_uk="Юбилейный"),
            VarietyFactory(name_uk="Їжакова Ґронка", name_en=""),
        ]

    @pytest.mark.parametrize(
        ("query", "expected"),
        [
            ("зоряний", ["Ранній Зоряний"]),
            ("STARRY", ["Ранній Зоряний"]),
            ("юбилейный", ["Ювілейний"]),  # Russian spelling from alt_names
            ("Юбилейни", ["Ювілейний"]),  # substring of an alternative name
            ("Зоряни", ["Ранній Зоряний"]),
            ("Ювелейний", ["Ювілейний"]),  # typo, found by trigram similarity
            ("ґронка", ["Їжакова Ґронка"]),
            ("абвгд", []),
        ],
    )
    def test_search_matches_names_in_any_language(self, varieties, query, expected):
        result = selectors.search_varieties(Variety.objects.all(), query)
        assert names(result) == expected

    def test_blank_query_returns_everything(self, varieties):
        assert selectors.search_varieties(Variety.objects.all(), "  ").count() == 3

    def test_better_matches_come_first(self):
        VarietyFactory(name_uk="Перлина Саби")
        VarietyFactory(name_uk="Перлина")
        result = selectors.search_varieties(Variety.objects.all(), "перлина")
        assert names(result)[0] == "Перлина"


class TestRangeOverlap:
    @pytest.fixture
    def varieties(self):
        return {
            "small": VarietyFactory(
                bunch_weight_min=Decimal("0.3"), bunch_weight_max=Decimal("0.5")
            ),
            "large": VarietyFactory(
                bunch_weight_min=Decimal("0.8"), bunch_weight_max=Decimal("1.5")
            ),
            "only_min": VarietyFactory(bunch_weight_min=Decimal("1.0")),
            "only_max": VarietyFactory(bunch_weight_max=Decimal("0.4")),
            "unknown": VarietyFactory(),
        }

    def matching(self, varieties, low, high) -> set[str]:
        result = selectors.filter_range_overlap(Variety.objects.all(), "bunch_weight", low, high)
        ids = set(result.values_list("pk", flat=True))
        return {key for key, variety in varieties.items() if variety.pk in ids}

    def test_lower_bound(self, varieties):
        assert self.matching(varieties, Decimal("0.6"), None) == {"large", "only_min"}

    def test_upper_bound(self, varieties):
        assert self.matching(varieties, None, Decimal("0.4")) == {"small", "only_max"}

    def test_both_bounds_keep_intersecting_ranges(self, varieties):
        assert self.matching(varieties, Decimal("0.45"), Decimal("0.9")) == {"small", "large"}

    def test_no_bounds_keep_everything(self, varieties):
        assert self.matching(varieties, None, None) == set(varieties)

    def test_single_value_characteristic(self):
        hardy = VarietyFactory(frost_resistance=-25)
        VarietyFactory(frost_resistance=-18)
        result = selectors.filter_range_overlap(Variety.objects.all(), "frost", None, -21)
        assert list(result) == [hardy]


class TestSimilarVarieties:
    def test_ranks_by_shared_characteristics_and_skips_unrelated(self):
        early, red, sweet = RipeningPeriodFactory(), BerryColorFactory(), TasteFactory()
        variety = VarietyFactory(ripening=early, berry_color=red, taste=sweet)
        same_color = VarietyFactory(berry_color=red, views_count=100)
        same_all = VarietyFactory(ripening=early, berry_color=red, taste=sweet)
        same_ripening = VarietyFactory(ripening=early)
        VarietyFactory()  # nothing in common
        VarietyFactory(ripening=early, is_published=False)

        assert selectors.similar_varieties(variety) == [same_all, same_ripening, same_color]

    def test_limit_and_popularity_break_ties(self):
        early = RipeningPeriodFactory()
        variety = VarietyFactory(ripening=early)
        popular = VarietyFactory(ripening=early, views_count=10)
        VarietyFactory(ripening=early, views_count=1)
        assert selectors.similar_varieties(variety, limit=1) == [popular]

    def test_variety_without_characteristics_has_no_similar(self):
        VarietyFactory()
        assert selectors.similar_varieties(VarietyFactory()) == []


def test_filter_options_return_dictionaries_and_published_bounds():
    early = RipeningPeriodFactory(name_uk="Надранній")
    VarietyFactory(
        bunch_weight_min=Decimal("0.4"), bunch_weight_max=Decimal("0.9"), frost_resistance=-21
    )
    VarietyFactory(
        bunch_weight_min=Decimal("0.6"), bunch_weight_max=Decimal("1.2"), frost_resistance=-24
    )
    VarietyFactory(bunch_weight_max=Decimal("3.0"), is_published=False)

    options = selectors.filter_options()

    assert options["ripening"] == list(RipeningPeriod.objects.all())
    assert early in options["ripening"]
    assert options["ranges"]["bunch_weight"] == selectors.NumberRange(
        Decimal("0.4"), Decimal("1.2")
    )
    assert options["ranges"]["frost"] == selectors.NumberRange(-24, -21)
    assert options["ranges"]["berry_size"] == selectors.NumberRange(None, None)


def test_available_letters_are_per_language_and_published_only():
    VarietyFactory(name_uk="Ювілейний", name_en="Jubilee")
    VarietyFactory(name_uk="Аркадія", name_en="")
    VarietyFactory(name_uk="Ґронка", name_en="Bunch")
    VarietyFactory(name_uk="12-34", name_en="12-34")
    VarietyFactory(name_uk="Ящірка", is_published=False)

    assert selectors.available_letters("uk") == ["А", "Ґ", "Ю", "#"]
    assert selectors.available_letters("en") == ["B", "J", "А", "#"]
    with translation.override("en"):
        assert selectors.available_letters() == ["B", "J", "А", "#"]


def test_current_language_falls_back_to_default():
    with translation.override("de"):
        assert selectors.current_language() == "uk"


def test_random_photos_come_from_published_varieties_only():
    published = VarietyPhotoFactory.create_batch(3)
    VarietyPhotoFactory(variety=VarietyFactory(is_published=False))

    photos = list(selectors.random_photos(10))

    assert sorted(photo.pk for photo in photos) == sorted(photo.pk for photo in published)
    assert len(selectors.random_photos(2)) == 2


def test_variety_list_puts_main_photo_first():
    variety = VarietyFactory()
    VarietyPhotoFactory(variety=variety, order=0)
    main = VarietyPhotoFactory(variety=variety, order=5, is_main=True)

    loaded = selectors.variety_list().get(pk=variety.pk)

    assert loaded.card_photos[0] == main
