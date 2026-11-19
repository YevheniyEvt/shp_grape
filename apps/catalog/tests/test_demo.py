import io

import pytest
from django.urls import reverse
from PIL import Image

from apps.catalog import demo
from apps.catalog.models import Variety, VarietyPhoto, VarietyVideo
from apps.catalog.tests.factories import VarietyFactory
from apps.core.slugs import slugify_uk

pytestmark = pytest.mark.django_db

LIST_URL = reverse("catalog:variety-list")


@pytest.fixture(autouse=True)
def _small_placeholders(monkeypatch):
    """Small placeholder photos keep the image renditions fast."""
    monkeypatch.setattr(demo, "PLACEHOLDER_SIZE", (120, 90))


@pytest.fixture
def no_own_photos(tmp_path):
    return tmp_path / "empty"


@pytest.fixture
def seeded(no_own_photos):
    return demo.seed_varieties(no_own_photos)


def make_file(path, image_format: str = "JPEG") -> None:
    buffer = io.BytesIO()
    Image.new("RGB", (30, 20), "green").save(buffer, image_format)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(buffer.getvalue())


def by_slug(slug: str) -> Variety:
    return Variety.objects.get(slug=slug)


def test_frozen_slugs_match_the_ukrainian_names():
    for item in demo.DEMO_VARIETIES:
        assert item.slug == slugify_uk(item.fields["name_uk"])


def test_demo_set_covers_the_planned_cases():
    items = demo.DEMO_VARIETIES
    assert 3 <= len(items) <= 5
    assert any(item.fields.get("is_featured") for item in items)
    assert any(not item.fields.get("description_uk") for item in items)
    assert any(item.photo_count == 0 for item in items)
    assert any(len(item.videos) == 2 for item in items)
    assert any(not item.fields.get("name_en") for item in items)
    assert all(item.photo_count == 0 or 3 <= item.photo_count <= 8 for item in items)


def test_seed_creates_varieties_photos_and_videos(seeded):
    assert sorted(seeded.created) == sorted(demo.DEMO_SLUGS)
    assert seeded.skipped == []
    expected_photos = sum(item.photo_count for item in demo.DEMO_VARIETIES)
    assert seeded.photos == expected_photos == VarietyPhoto.objects.count()

    featured = by_slug("rankovyi-ametyst")
    assert featured.is_featured
    assert featured.ripening.slug == "duzhe-rannii"
    assert featured.videos.count() == 2
    assert featured.photos.filter(is_main=True).count() == 1
    assert featured.photos.get(is_main=True).order == 0

    out_of_stock = by_slug("nichnyi-sapfir")
    assert not out_of_stock.cutting_available
    assert not out_of_stock.sapling_available
    assert out_of_stock.description == ""

    assert by_slug("bilyi-tuman").photos.count() == 0
    assert by_slug("stepovyi-rubin").name_en is None


def test_placeholder_photos_get_webp_renditions(seeded):
    photo = by_slug("burshtynova-zoria").photos.first()
    assert photo.image.name.endswith(".jpg")
    assert photo.thumb.url.endswith(".webp")
    assert photo.alt_uk == "Бурштинова Зоря, фото 1"
    assert photo.alt_en == "Amber Dawn, photo 1"


def test_variety_without_english_name_has_no_english_alt(seeded):
    photo = by_slug("stepovyi-rubin").photos.first()
    assert photo.alt_en is None


def test_seed_twice_creates_no_duplicates(no_own_photos, seeded):
    again = demo.seed_varieties(no_own_photos)

    assert again.created == []
    assert sorted(again.skipped) == sorted(demo.DEMO_SLUGS)
    assert again.photos == 0
    assert Variety.objects.count() == len(demo.DEMO_VARIETIES)
    assert VarietyPhoto.objects.count() == seeded.photos
    assert VarietyVideo.objects.count() == 2


def test_seed_keeps_admin_edits(no_own_photos, seeded):
    Variety.objects.filter(slug="bilyi-tuman").update(cutting_available=False)
    demo.seed_varieties(no_own_photos)
    assert by_slug("bilyi-tuman").cutting_available is False


def test_own_photos_replace_placeholders(tmp_path):
    folder = tmp_path / "rankovyi-ametyst"
    make_file(folder / "b.png", "PNG")
    make_file(folder / "a.jpg")
    (folder / "notes.txt").write_text("not a photo")
    (folder / "nested").mkdir()

    report = demo.seed_varieties(tmp_path)

    names = [
        photo.image.name.rsplit("/", 1)[-1] for photo in by_slug("rankovyi-ametyst").photos.all()
    ]
    assert names == ["a.jpg", "b.png"]
    # The other varieties still get placeholders.
    assert by_slug("stepovyi-rubin").photos.count() == 3
    assert report.photos == 2 + 4 + 3 + 3


def test_find_photo_files_without_folder(tmp_path):
    assert demo.find_photo_files("missing", tmp_path) == []


@pytest.mark.parametrize("berry_color", ["chervonyi", "unknown"])
def test_placeholder_photo_is_a_jpeg(berry_color):
    content = demo.placeholder_photo("Test", berry_color, 2)
    image = Image.open(io.BytesIO(content))
    assert image.format == "JPEG"
    assert image.size == (120, 90)


def test_placeholders_differ_between_photos():
    assert demo.placeholder_photo("Test", "synii", 1) != demo.placeholder_photo("Test", "synii", 2)


def test_delete_demo_varieties_keeps_other_varieties(seeded):
    own = VarietyFactory()

    assert demo.delete_demo_varieties() == len(demo.DEMO_VARIETIES)
    assert list(Variety.objects.all()) == [own]
    assert VarietyPhoto.objects.count() == 0


def test_english_api_falls_back_to_ukrainian_name(api_client, seeded):
    response = api_client.get(
        reverse("catalog:variety-detail", args=["stepovyi-rubin"]), HTTP_ACCEPT_LANGUAGE="en"
    )
    assert response.json()["name"] == "Степовий Рубін"


# Every catalog filter returns something on one parameter set and nothing on another.
FILTER_CASES = [
    ("letter", {"letter": "Р"}, {"letter": "Я"}),
    ("search", {"search": "аметист"}, {"search": "zzzz"}),
    ("ripening", {"ripening": "rannii"}, {"ripening": "duzhe-piznii"}),
    ("berry_color", {"berry_color": "zhovtyi"}, {"berry_color": "rozhevyi"}),
    ("pulp", {"pulp": "khrustka"}, {"pulp": "khrustka", "ripening": "piznii"}),
    ("taste", {"taste": "muskatnyi"}, {"taste": "izabelnyi"}),
    ("vigor", {"vigor": "slaborosla"}, {"vigor": "slaborosla", "ripening": "piznii"}),
    ("bunch_weight_min", {"bunch_weight_min": "1"}, {"bunch_weight_min": "5"}),
    ("bunch_weight_max", {"bunch_weight_max": "0.35"}, {"bunch_weight_max": "0.1"}),
    ("berry_weight_min", {"berry_weight_min": "12"}, {"berry_weight_min": "50"}),
    ("berry_weight_max", {"berry_weight_max": "5"}, {"berry_weight_max": "1"}),
    ("berry_size_min", {"berry_size_min": "30"}, {"berry_size_min": "60"}),
    ("berry_size_max", {"berry_size_max": "19"}, {"berry_size_max": "10"}),
    ("disease_min", {"disease_min": "3.8"}, {"disease_min": "4.5"}),
    ("disease_max", {"disease_max": "2.1"}, {"disease_max": "1"}),
    ("frost_min", {"frost_min": "-22"}, {"frost_min": "0"}),
    ("frost_max", {"frost_max": "-25"}, {"frost_max": "-30"}),
    ("in_stock", {"in_stock": "false"}, {"in_stock": "false", "featured": "true"}),
    ("featured", {"featured": "true"}, {"featured": "true", "ripening": "piznii"}),
]


@pytest.mark.parametrize(
    ("name", "matching", "empty"), FILTER_CASES, ids=[c[0] for c in FILTER_CASES]
)
def test_every_filter_has_matching_and_empty_results(api_client, seeded, name, matching, empty):
    total = len(demo.DEMO_VARIETIES)
    found = api_client.get(LIST_URL, matching).json()["count"]
    assert 0 < found < total
    assert api_client.get(LIST_URL, empty).json()["count"] == 0


def test_filter_cases_cover_every_filter():
    from apps.catalog.filters import VarietyFilter

    filters = set(VarietyFilter.base_filters) - {"ordering"}
    assert {case[0] for case in FILTER_CASES} == filters
