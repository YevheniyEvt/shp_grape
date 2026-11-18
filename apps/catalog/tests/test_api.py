from decimal import Decimal

import pytest
from django.core.cache import cache
from django.core.management import call_command
from django.urls import reverse
from time_machine import travel

from apps.catalog.models import BerryColor, RipeningPeriod
from apps.catalog.tests.factories import (
    BerryColorFactory,
    GrowthVigorFactory,
    PulpConsistencyFactory,
    RipeningPeriodFactory,
    TasteFactory,
    VarietyFactory,
    VarietyPhotoFactory,
    VarietyVideoFactory,
)

pytestmark = pytest.mark.django_db

LIST_URL = reverse("catalog:variety-list")


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()


def detail_url(slug: str) -> str:
    return reverse("catalog:variety-detail", kwargs={"slug": slug})


def list_slugs(api_client, **params) -> list[str]:
    response = api_client.get(LIST_URL, params)
    assert response.status_code == 200, response.content
    return [item["slug"] for item in response.json()["results"]]


class TestVarietyList:
    def test_card_fields_follow_accept_language(self, api_client, language):
        ripening = RipeningPeriodFactory(name_uk="Ранній", name_en="Early")
        variety = VarietyFactory(
            name_uk="Ювілейний",
            name_en="Jubilee",
            ripening=ripening,
            cutting_price=Decimal("50.00"),
            cutting_available=True,
        )
        VarietyPhotoFactory(variety=variety, alt_uk="Грона", alt_en="Bunches", is_main=True)

        response = api_client.get(LIST_URL, HTTP_ACCEPT_LANGUAGE=language)

        item = response.json()["results"][0]
        expected = {"uk": ("Ювілейний", "Ранній", "Грона"), "en": ("Jubilee", "Early", "Bunches")}
        assert (item["name"], item["ripening"]["name"], item["main_photo"]["alt"]) == expected[
            language
        ]
        assert item["ripening"]["slug"] == ripening.slug
        assert item["cutting_price"] == 50.0
        assert item["main_photo"]["thumb"].startswith("http://testserver/")
        assert item["main_photo"]["thumb"].endswith(".webp")
        assert {"medium", "large", "width", "height"} <= set(item["main_photo"])

    def test_untranslated_values_fall_back_to_ukrainian(self, api_client):
        VarietyFactory(name_uk="Ювілейний", name_en="")
        response = api_client.get(LIST_URL, HTTP_ACCEPT_LANGUAGE="en")
        assert response.json()["results"][0]["name"] == "Ювілейний"

    def test_photo_alt_falls_back_to_variety_name(self, api_client):
        VarietyPhotoFactory(variety=VarietyFactory(name_uk="Ювілейний"), alt_uk="")
        response = api_client.get(LIST_URL)
        assert response.json()["results"][0]["main_photo"]["alt"] == "Ювілейний"

    def test_variety_without_photos_has_no_main_photo(self, api_client):
        VarietyFactory()
        assert api_client.get(LIST_URL).json()["results"][0]["main_photo"] is None

    def test_unpublished_varieties_are_hidden(self, api_client):
        visible = VarietyFactory()
        VarietyFactory(is_published=False)
        assert list_slugs(api_client) == [visible.slug]

    def test_pagination_defaults_to_24_and_accepts_page_size(self, api_client):
        VarietyFactory.create_batch(26)
        response = api_client.get(LIST_URL).json()
        assert (response["count"], len(response["results"])) == (26, 24)
        assert len(api_client.get(LIST_URL, {"page_size": 5}).json()["results"]) == 5
        assert len(api_client.get(LIST_URL, {"page": 2}).json()["results"]) == 2

    def test_list_of_24_varieties_uses_few_queries(self, api_client, django_assert_max_num_queries):
        for variety in VarietyFactory.create_batch(
            24, ripening=RipeningPeriodFactory(), berry_color=BerryColorFactory()
        ):
            VarietyPhotoFactory.create_batch(2, variety=variety)

        with django_assert_max_num_queries(5):
            response = api_client.get(LIST_URL)

        assert len(response.json()["results"]) == 24


class TestVarietyFilters:
    def test_letter_uses_current_language(self, api_client):
        jubilee = VarietyFactory(name_uk="Ювілейний", name_en="Jubilee")
        arcadia = VarietyFactory(name_uk="Аркадія", name_en="Arcadia")
        code = VarietyFactory(name_uk="12-34", name_en="")
        assert list_slugs(api_client, letter="ю") == [jubilee.slug]
        assert list_slugs(api_client, letter="#") == [code.slug]
        assert list_slugs(api_client, letter="1") == [code.slug]
        response = api_client.get(LIST_URL, {"letter": "A"}, HTTP_ACCEPT_LANGUAGE="en")
        assert [item["slug"] for item in response.json()["results"]] == [arcadia.slug]

    def test_blank_filter_values_are_ignored(self, api_client):
        VarietyFactory.create_batch(2)
        assert len(list_slugs(api_client, letter=" ", bunch_weight_min="", search="")) == 2

    def test_search(self, api_client):
        variety = VarietyFactory(name_uk="Ювілейний", alt_names_uk="Юбилейный")
        VarietyFactory(name_uk="Аркадія")
        assert list_slugs(api_client, search="юбилейный") == [variety.slug]

    @pytest.mark.parametrize(
        ("param", "factory"),
        [
            ("ripening", RipeningPeriodFactory),
            ("berry_color", BerryColorFactory),
            ("pulp", PulpConsistencyFactory),
            ("taste", TasteFactory),
            ("vigor", GrowthVigorFactory),
        ],
    )
    def test_dictionary_filters_accept_several_slugs(self, api_client, param, factory):
        first, second, third = factory.create_batch(3)
        expected = {
            VarietyFactory(**{param: first}).slug,
            VarietyFactory(**{param: second}).slug,
        }
        VarietyFactory(**{param: third})
        VarietyFactory()

        assert set(list_slugs(api_client, **{param: [first.slug, second.slug]})) == expected

    def test_unknown_dictionary_slug_is_a_validation_error(self, api_client):
        response = api_client.get(LIST_URL, {"ripening": "nope"})
        assert response.status_code == 400

    @pytest.mark.parametrize(
        ("param", "fields", "inside", "outside"),
        [
            (
                "bunch_weight",
                ("bunch_weight_min", "bunch_weight_max"),
                ("0.5", "1.0"),
                ("1.5", "2"),
            ),
            ("berry_weight", ("berry_weight_min", "berry_weight_max"), ("6", "8"), ("12", "15")),
            ("berry_size", ("berry_size_min", "berry_size_max"), ("20", "25"), ("30", "35")),
            (
                "disease",
                ("disease_susceptibility_min", "disease_susceptibility_max"),
                ("2", "2.5"),
                ("3.5", "4"),
            ),
        ],
    )
    def test_range_filters(self, api_client, param, fields, inside, outside):
        low_field, high_field = fields
        match = VarietyFactory(**{low_field: inside[0], high_field: inside[1]})
        VarietyFactory(**{low_field: outside[0], high_field: outside[1]})

        params = {f"{param}_min": inside[0], f"{param}_max": inside[1]}
        assert list_slugs(api_client, **params) == [match.slug]

    def test_frost_filters(self, api_client):
        hardy = VarietyFactory(frost_resistance=-25)
        tender = VarietyFactory(frost_resistance=-18)
        assert list_slugs(api_client, frost_max=-22) == [hardy.slug]
        assert list_slugs(api_client, frost_min=-20) == [tender.slug]

    def test_in_stock(self, api_client):
        cutting = VarietyFactory(cutting_available=True)
        sapling = VarietyFactory(sapling_available=True)
        none = VarietyFactory()
        assert set(list_slugs(api_client, in_stock="true")) == {cutting.slug, sapling.slug}
        assert list_slugs(api_client, in_stock="false") == [none.slug]

    def test_featured(self, api_client):
        featured = VarietyFactory(is_featured=True)
        VarietyFactory()
        assert list_slugs(api_client, featured="true") == [featured.slug]


class TestVarietyOrdering:
    def test_default_ordering_is_by_localized_name(self, api_client):
        a = VarietyFactory(name_uk="Аркадія", name_en="Zeta")
        b = VarietyFactory(name_uk="Ювілейний", name_en="Alpha")
        assert list_slugs(api_client) == [a.slug, b.slug]
        response = api_client.get(LIST_URL, HTTP_ACCEPT_LANGUAGE="en")
        assert [item["slug"] for item in response.json()["results"]] == [b.slug, a.slug]

    def test_untranslated_names_sort_by_their_fallback(self, api_client):
        bravo = VarietyFactory(name_uk="Браво", name_en="Bravo")
        untranslated = VarietyFactory(name_uk="Аркадія", name_en="")
        response = api_client.get(LIST_URL, HTTP_ACCEPT_LANGUAGE="en")
        assert [item["slug"] for item in response.json()["results"]] == [
            bravo.slug,
            untranslated.slug,
        ]

    def test_ordering_by_ripening_puts_unknown_last(self, api_client):
        late = VarietyFactory(name_uk="А", ripening=RipeningPeriodFactory(order=2))
        unknown = VarietyFactory(name_uk="Б")
        early = VarietyFactory(name_uk="В", ripening=RipeningPeriodFactory(order=1))
        assert list_slugs(api_client, ordering="ripening") == [early.slug, late.slug, unknown.slug]

    def test_ordering_by_newest(self, api_client):
        with travel("2026-01-01"):
            old = VarietyFactory()
        with travel("2026-02-01"):
            new = VarietyFactory()
        assert list_slugs(api_client, ordering="-created") == [new.slug, old.slug]

    def test_ordering_by_views(self, api_client):
        quiet = VarietyFactory(views_count=1)
        popular = VarietyFactory(views_count=10)
        assert list_slugs(api_client, ordering="-views_count") == [popular.slug, quiet.slug]

    def test_explicit_ordering_overrides_search_rank(self, api_client):
        VarietyFactory(name_uk="Перлина Саби")
        VarietyFactory(name_uk="Перлина")
        by_rank = list_slugs(api_client, search="перлина")
        by_name = list_slugs(api_client, search="перлина", ordering="-views_count")
        assert by_rank[0] == "perlyna"
        assert set(by_name) == set(by_rank)

    def test_unknown_ordering_is_rejected(self, api_client):
        assert api_client.get(LIST_URL, {"ordering": "price"}).status_code == 400


class TestVarietyDetail:
    def test_full_variety_in_requested_language(self, api_client, language):
        ripening = RipeningPeriodFactory()
        variety = VarietyFactory(
            name_uk="Ювілейний",
            name_en="Jubilee",
            description_uk="<p>Опис</p>",
            description_en="<p>Description</p>",
            ripening=ripening,
            pulp=PulpConsistencyFactory(),
        )
        VarietyPhotoFactory.create_batch(2, variety=variety)
        VarietyVideoFactory(variety=variety)
        similar = VarietyFactory(ripening=ripening)

        response = api_client.get(detail_url(variety.slug), HTTP_ACCEPT_LANGUAGE=language)

        assert response.status_code == 200
        data = response.json()
        expected = {
            "uk": ("Ювілейний", "<p>Опис</p>", "Огляд сорту"),
            "en": ("Jubilee", "<p>Description</p>", "Variety review"),
        }
        assert (data["name"], data["description"], data["videos"][0]["title"]) == expected[language]
        assert len(data["photos"]) == 2
        assert data["videos"][0]["youtube_id"] == "dQw4w9WgXcQ"
        assert data["pulp"]["slug"] == variety.pulp.slug
        assert data["taste"] is None
        assert [item["slug"] for item in data["similar"]] == [similar.slug]

    def test_unpublished_variety_is_not_found(self, api_client):
        variety = VarietyFactory(is_published=False)
        assert api_client.get(detail_url(variety.slug)).status_code == 404

    def test_unknown_slug_is_not_found(self, api_client):
        assert api_client.get(detail_url("nope")).status_code == 404


class TestViewCounter:
    def test_view_is_counted_once_per_visitor(self, api_client):
        variety = VarietyFactory()
        url = reverse("catalog:variety-view", kwargs={"slug": variety.slug})

        assert api_client.post(url).json() == {"counted": True}
        assert api_client.post(url).json() == {"counted": False}
        assert api_client.post(url, REMOTE_ADDR="10.0.0.2").json() == {"counted": True}
        variety.refresh_from_db()
        assert variety.views_count == 2

    def test_unpublished_variety_is_not_found(self, api_client):
        variety = VarietyFactory(is_published=False)
        url = reverse("catalog:variety-view", kwargs={"slug": variety.slug})
        assert api_client.post(url).status_code == 404


def test_filter_options(api_client, language):
    RipeningPeriodFactory(name_uk="Надранній", name_en="Ultra early", order=0)
    VarietyFactory(berry_weight_min=Decimal(6), berry_weight_max=Decimal(9), frost_resistance=-23)

    response = api_client.get(reverse("catalog:filters"), HTTP_ACCEPT_LANGUAGE=language)

    assert response.status_code == 200
    data = response.json()
    # Default values from the data migration follow the new one (order 0 comes first).
    assert data["ripening"][0] == {
        "slug": "nadrannii",
        "name": {"uk": "Надранній", "en": "Ultra early"}[language],
    }
    assert len(data["ripening"]) == RipeningPeriod.objects.count()
    assert [item["slug"] for item in data["berry_color"]] == list(
        BerryColor.objects.values_list("slug", flat=True)
    )
    assert data["ranges"]["berry_weight"] == {"min": 6.0, "max": 9.0}
    assert data["ranges"]["frost"] == {"min": -23.0, "max": -23.0}
    assert data["ranges"]["bunch_weight"] == {"min": None, "max": None}


def test_letters(api_client):
    VarietyFactory(name_uk="Ювілейний", name_en="Jubilee")
    VarietyFactory(name_uk="Аркадія", name_en="Arcadia")

    assert api_client.get(reverse("catalog:letters")).json() == ["А", "Ю"]
    response = api_client.get(reverse("catalog:letters"), HTTP_ACCEPT_LANGUAGE="en")
    assert response.json() == ["A", "J"]


class TestRandomPhotos:
    url = reverse("catalog:random-photos")

    def test_returns_thumbnails_linked_to_varieties(self, api_client):
        photo = VarietyPhotoFactory(variety=VarietyFactory(name_uk="Ювілейний"))
        data = api_client.get(self.url).json()
        assert data == [
            {
                "id": photo.pk,
                "alt": "Ювілейний",
                "width": 40,
                "height": 30,
                "thumb": f"http://testserver{photo.thumb.url}",
                "variety": {"slug": "yuvileinyi", "name": "Ювілейний"},
            }
        ]

    @pytest.mark.parametrize(
        ("limit", "expected"), [(None, 10), ("3", 3), ("0", 1), ("100", 12), ("abc", 10)]
    )
    def test_limit_is_clamped(self, api_client, limit, expected, monkeypatch):
        monkeypatch.setattr("apps.catalog.views.RANDOM_PHOTOS_MAX", 12)
        VarietyPhotoFactory.create_batch(13)
        params = {"limit": limit} if limit is not None else {}
        assert len(api_client.get(self.url, params).json()) == expected


def test_openapi_schema_has_no_warnings(tmp_path):
    call_command(
        "spectacular", "--validate", "--fail-on-warn", "--file", str(tmp_path / "schema.yml")
    )
