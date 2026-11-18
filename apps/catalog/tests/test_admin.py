import io
from html.parser import HTMLParser

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from apps.catalog.admin import MultipleImageField
from apps.catalog.models import RipeningPeriod, Variety
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


def make_image(name: str) -> SimpleUploadedFile:
    buffer = io.BytesIO()
    Image.new("RGB", (20, 10), "green").save(buffer, "JPEG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/jpeg")


@pytest.mark.parametrize(
    "factory",
    [
        RipeningPeriodFactory,
        BerryColorFactory,
        PulpConsistencyFactory,
        TasteFactory,
        GrowthVigorFactory,
        VarietyFactory,
    ],
)
def test_admin_pages_open(admin_client, factory):
    obj = factory()
    if isinstance(obj, Variety):
        VarietyPhotoFactory(variety=obj, is_main=True)
        VarietyVideoFactory(variety=obj)
    opts = obj._meta
    base = f"admin:{opts.app_label}_{opts.model_name}"

    assert admin_client.get(reverse(f"{base}_changelist")).status_code == 200
    assert admin_client.get(reverse(f"{base}_add")).status_code == 200
    assert admin_client.get(reverse(f"{base}_change", args=[obj.pk])).status_code == 200


def test_variety_changelist_search(admin_client):
    VarietyFactory(name_uk="Ювілейний")
    response = admin_client.get(reverse("admin:catalog_variety_changelist"), {"q": "ювіл"})
    assert response.status_code == 200
    assert "Ювілейний" in response.content.decode()


def inline_management(prefix: str) -> dict[str, str]:
    return {
        f"{prefix}-TOTAL_FORMS": "0",
        f"{prefix}-INITIAL_FORMS": "0",
        f"{prefix}-MIN_NUM_FORMS": "0",
        f"{prefix}-MAX_NUM_FORMS": "1000",
    }


def test_variety_is_created_with_bulk_uploaded_photos(admin_client):
    data = {
        "name_uk": "Ювілейний",
        "name_en": "Jubilee",
        "is_published": "on",
        "upload_photos": [make_image("a.jpg"), make_image("b.jpg"), make_image("c.jpg")],
        **inline_management("photos"),
        **inline_management("videos"),
    }

    response = admin_client.post(reverse("admin:catalog_variety_add"), data)

    assert response.status_code == 302, response.context["adminform"].form.errors
    variety = Variety.objects.get(slug="yuvileinyi")
    photos = list(variety.photos.order_by("order"))
    assert [photo.order for photo in photos] == [0, 1, 2]
    assert photos[0].is_main is True


def test_multiple_image_field_validates_each_file():
    field = MultipleImageField(required=False)
    assert field.clean([]) == []
    assert field.clean(None) == []
    assert len(field.clean([make_image("a.jpg"), make_image("b.jpg")])) == 2
    assert len(field.clean(make_image("a.jpg"))) == 1
    broken = SimpleUploadedFile("x.jpg", b"not an image", content_type="image/jpeg")
    with pytest.raises(ValidationError) as error:
        field.clean([broken])
    assert error.value.code == "invalid_image"


class FormParser(HTMLParser):
    """Collect the values a browser would submit for the form fields of a page."""

    def __init__(self) -> None:
        super().__init__()
        self.data: dict[str, str] = {}
        self._textarea: str | None = None
        self._select: str | None = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        name = attrs.get("name")
        if tag == "input" and name and attrs.get("type") not in {"submit", "button", "file"}:
            if attrs.get("type") != "checkbox":
                self.data[name] = attrs.get("value") or ""
            elif "checked" in attrs:
                self.data[name] = "on"
        elif tag == "textarea" and name:
            self._textarea = name
            self.data[name] = ""
        elif tag == "select" and name:
            self._select = name
            self.data.setdefault(name, "")
        elif tag == "option" and self._select and "selected" in attrs:
            self.data[self._select] = attrs.get("value") or ""

    def handle_endtag(self, tag):
        if tag == "textarea":
            self._textarea = None
        elif tag == "select":
            self._select = None

    def handle_data(self, data):
        if self._textarea:
            self.data[self._textarea] += data


def form_data(admin_client, url: str) -> dict[str, str]:
    parser = FormParser()
    parser.feed(admin_client.get(url).content.decode())
    return {name: value for name, value in parser.data.items() if "__prefix__" not in name}


def test_main_photo_can_be_moved_to_another_photo(admin_client):
    variety = VarietyFactory()
    first = VarietyPhotoFactory(variety=variety, is_main=True, order=0)
    second = VarietyPhotoFactory(variety=variety, order=1)
    url = reverse("admin:catalog_variety_change", args=[variety.pk])
    data = form_data(admin_client, url)
    data.pop("photos-0-is_main")
    data["photos-1-is_main"] = "on"

    response = admin_client.post(url, data)

    assert response.status_code == 302
    first.refresh_from_db()
    second.refresh_from_db()
    assert (first.is_main, second.is_main) == (False, True)


def test_second_main_photo_replaces_the_first_one(admin_client):
    variety = VarietyFactory()
    first = VarietyPhotoFactory(variety=variety, is_main=True, order=0)
    second = VarietyPhotoFactory(variety=variety, order=1)
    url = reverse("admin:catalog_variety_change", args=[variety.pk])
    data = form_data(admin_client, url) | {"photos-1-is_main": "on"}

    assert admin_client.post(url, data).status_code == 302
    first.refresh_from_db()
    second.refresh_from_db()
    assert second.is_main is True
    assert first.is_main is False


def test_variety_with_photo_and_video_rows_is_saved(admin_client):
    url = reverse("admin:catalog_variety_add")
    data = form_data(admin_client, url) | {
        "name_uk": "Ювілейний",
        "photos-TOTAL_FORMS": "1",
        "photos-0-image": make_image("a.jpg"),
        "photos-0-alt_uk": "Грона",
        "videos-TOTAL_FORMS": "1",
        "videos-0-youtube_url": "https://youtu.be/dQw4w9WgXcQ",
    }

    assert admin_client.post(url, data).status_code == 302
    variety = Variety.objects.get(slug="yuvileinyi")
    assert variety.photos.count() == 1
    assert variety.videos.get().youtube_id == "dQw4w9WgXcQ"


def test_admin_is_ukrainian_whatever_the_browser_language(admin_client):
    url = reverse("admin:catalog_variety_add")
    html = admin_client.get(url, HTTP_ACCEPT_LANGUAGE="en").content.decode()
    assert "Додати сорт" in html
    assert "Характеристики" in html


def test_api_still_follows_browser_language(api_client):
    VarietyFactory(name_uk="Ювілейний", name_en="Jubilee")
    response = api_client.get(reverse("catalog:variety-list"), HTTP_ACCEPT_LANGUAGE="en")
    assert response.json()["results"][0]["name"] == "Jubilee"


def test_rich_text_editor_gets_admin_styles(admin_client):
    html = admin_client.get(reverse("admin:catalog_variety_add")).content.decode()
    assert "core/admin.css" in html


@pytest.mark.parametrize(
    "url_name", ["admin:catalog_variety_add", "admin:catalog_ripeningperiod_add"]
)
def test_add_form_does_not_ask_for_slug(admin_client, url_name):
    html = admin_client.get(reverse(url_name)).content.decode()
    assert 'name="slug"' not in html


def test_change_form_shows_slug_read_only_and_ignores_posted_slug(admin_client):
    variety = VarietyFactory(name_uk="Ювілейний")
    url = reverse("admin:catalog_variety_change", args=[variety.pk])
    html = admin_client.get(url).content.decode()
    assert 'name="slug"' not in html
    assert "yuvileinyi" in html

    data = form_data(admin_client, url) | {"slug": "hacked", "name_uk": "Новий"}
    assert admin_client.post(url, data).status_code == 302
    variety.refresh_from_db()
    assert (variety.name_uk, variety.slug) == ("Новий", "yuvileinyi")


def test_dictionary_is_created_without_slug(admin_client):
    url = reverse("admin:catalog_ripeningperiod_add")
    data = form_data(admin_client, url) | {"name_uk": "Надранній"}
    assert admin_client.post(url, data).status_code == 302
    assert RipeningPeriod.objects.get(name_uk="Надранній").slug == "nadrannii"
