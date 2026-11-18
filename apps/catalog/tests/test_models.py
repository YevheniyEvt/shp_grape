from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import translation

from apps.catalog.models import RipeningPeriod, Variety, VarietyPhoto, variety_photo_path
from apps.catalog.tests.factories import (
    RipeningPeriodFactory,
    VarietyFactory,
    VarietyPhotoFactory,
    VarietyVideoFactory,
)

pytestmark = pytest.mark.django_db


class TestVariety:
    def test_first_letter_is_stored_per_language(self):
        variety = VarietyFactory(name_uk="Ювілейний", name_en="Jubilee")
        assert (variety.first_letter_uk, variety.first_letter_en) == ("Ю", "J")

    def test_first_letter_falls_back_to_ukrainian_name(self):
        variety = VarietyFactory(name_uk="Ювілейний", name_en="")
        assert variety.first_letter_en == "Ю"

    def test_first_letter_follows_rename_with_update_fields(self):
        variety = VarietyFactory(name_uk="Ювілейний", name_en="Jubilee")
        variety.name_en = "Anniversary"
        variety.save(update_fields=["name_en"])
        variety.refresh_from_db()
        assert variety.first_letter_en == "A"

    def test_save_with_unrelated_update_fields_keeps_them(self):
        variety = VarietyFactory()
        variety.is_featured = True
        variety.save(update_fields=["is_featured"])
        variety.refresh_from_db()
        assert variety.is_featured is True

    def test_translated_name_falls_back_to_ukrainian(self):
        variety = VarietyFactory(name_uk="Ювілейний", name_en="")
        with translation.override("en"):
            assert Variety.objects.get(pk=variety.pk).name == "Ювілейний"
        assert str(variety) == "Ювілейний"

    @pytest.mark.parametrize(
        "field", ["bunch_weight", "berry_weight", "berry_size", "disease_susceptibility"]
    )
    def test_clean_rejects_inverted_range(self, field):
        variety = VarietyFactory.build(**{f"{field}_min": Decimal(5), f"{field}_max": Decimal(1)})
        with pytest.raises(ValidationError) as error:
            variety.clean()
        assert f"{field}_max" in error.value.message_dict

    def test_clean_accepts_open_and_equal_ranges(self):
        variety = VarietyFactory.build(
            bunch_weight_min=Decimal("0.5"),
            bunch_weight_max=Decimal("0.5"),
            berry_weight_min=Decimal(8),
        )
        variety.clean()

    def test_database_rejects_inverted_range(self):
        with pytest.raises(IntegrityError):
            VarietyFactory(berry_size_min=Decimal(30), berry_size_max=Decimal(20))

    def test_natural_key(self):
        variety = VarietyFactory(name_uk="Ювілейний")
        assert variety.natural_key() == ("yuvileinyi",)
        assert Variety.objects.get_by_natural_key("yuvileinyi") == variety

    def test_rich_text_description_is_sanitized(self):
        variety = VarietyFactory.build(
            name_uk="Тест",
            description_uk='<p onclick="x()">Hi<script>alert(1)</script></p>',
        )
        variety.full_clean()
        assert variety.description_uk == "<p>Hi</p>"


class TestDictionary:
    def test_ordering_and_natural_key(self):
        late = RipeningPeriodFactory(name_uk="Запізнілий", order=2)
        early = RipeningPeriodFactory(name_uk="Надранній", order=1)
        ours = RipeningPeriod.objects.filter(pk__in=[early.pk, late.pk])
        assert list(ours) == [early, late]
        assert early.natural_key() == ("nadrannii",)
        assert RipeningPeriod.objects.get_by_natural_key("nadrannii") == early
        assert str(early) == "Надранній"


class TestVarietyPhoto:
    def test_dimensions_are_stored(self):
        photo = VarietyPhotoFactory()
        assert (photo.width, photo.height) == (40, 30)

    def test_upload_path_uses_variety_slug(self):
        variety = VarietyFactory(name_uk="Ювілейний")
        photo = VarietyPhoto(variety=variety)
        assert variety_photo_path(photo, "C:/tmp/photo.jpg") == "varieties/yuvileinyi/photo.jpg"

    def test_webp_renditions_are_generated(self):
        photo = VarietyPhotoFactory()
        for spec in (photo.thumb, photo.medium, photo.large):
            assert spec.url.endswith(".webp")
            assert spec.storage.exists(spec.name)

    def test_marking_main_photo_unmarks_the_previous_one(self):
        first = VarietyPhotoFactory(is_main=True)
        second = VarietyPhotoFactory(variety=first.variety, is_main=True)
        first.refresh_from_db()
        assert (first.is_main, second.is_main) == (False, True)

    def test_main_photos_of_different_varieties_are_independent(self):
        first = VarietyPhotoFactory(is_main=True)
        VarietyPhotoFactory(is_main=True)
        first.refresh_from_db()
        assert first.is_main is True

    def test_str_prefers_alt_text(self):
        photo = VarietyPhotoFactory(alt_uk="Грона")
        assert str(photo) == "Грона"
        photo.alt_uk = ""
        assert str(photo).endswith(".jpg")


class TestVarietyVideo:
    def test_youtube_id_is_extracted_on_save(self):
        video = VarietyVideoFactory(youtube_url="https://youtu.be/dQw4w9WgXcQ")
        assert video.youtube_id == "dQw4w9WgXcQ"
        assert str(video) == "Огляд сорту"

    def test_invalid_link_is_rejected(self):
        with pytest.raises(ValidationError):
            VarietyVideoFactory(youtube_url="https://vimeo.com/1")

    def test_str_falls_back_to_link(self):
        video = VarietyVideoFactory(title_uk="", title_en="")
        assert str(video) == video.youtube_url


@pytest.mark.parametrize(("language", "expected"), [("uk", "сорт"), ("en", "variety")])
def test_model_names_are_translated(language, expected):
    with translation.override(language):
        assert str(Variety._meta.verbose_name) == expected
