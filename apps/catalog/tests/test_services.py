import io

import pytest
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.catalog import services
from apps.catalog.tests.factories import VarietyFactory, VarietyPhotoFactory

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


def make_image(name: str = "photo.jpg") -> SimpleUploadedFile:
    buffer = io.BytesIO()
    Image.new("RGB", (20, 10), "green").save(buffer, "JPEG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/jpeg")


class TestRegisterView:
    def test_first_view_is_counted(self):
        variety = VarietyFactory()
        assert services.register_view(variety, "1.2.3.4|ua") is True
        variety.refresh_from_db()
        assert variety.views_count == 1

    def test_repeated_view_of_same_visitor_is_ignored(self):
        variety = VarietyFactory()
        services.register_view(variety, "1.2.3.4|ua")
        assert services.register_view(variety, "1.2.3.4|ua") is False
        variety.refresh_from_db()
        assert variety.views_count == 1

    def test_other_visitors_and_varieties_are_counted_separately(self):
        first, second = VarietyFactory(), VarietyFactory()
        services.register_view(first, "1.2.3.4|ua")
        services.register_view(first, "5.6.7.8|ua")
        services.register_view(second, "1.2.3.4|ua")
        first.refresh_from_db()
        second.refresh_from_db()
        assert (first.views_count, second.views_count) == (2, 1)

    def test_cache_key_does_not_contain_visitor_data(self):
        key = services._view_cache_key(1, "1.2.3.4|Mozilla")
        assert "1.2.3.4" not in key
        assert "Mozilla" not in key


class TestAddPhotos:
    def test_first_photo_becomes_main_when_variety_has_none(self):
        variety = VarietyFactory()
        photos = services.add_photos(variety, [make_image("a.jpg"), make_image("b.jpg")])
        assert [photo.order for photo in photos] == [0, 1]
        assert [photo.is_main for photo in photos] == [True, False]

    def test_photos_are_appended_after_existing_ones(self):
        existing = VarietyPhotoFactory(order=7, is_main=True)
        photos = services.add_photos(existing.variety, [make_image()])
        assert photos[0].order == 8
        assert photos[0].is_main is False
        existing.refresh_from_db()
        assert existing.is_main is True

    def test_no_files_create_nothing(self):
        variety = VarietyFactory()
        assert services.add_photos(variety, []) == []
        assert variety.photos.count() == 0
