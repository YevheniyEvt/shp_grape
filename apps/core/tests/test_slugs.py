import re

import pytest
from hypothesis import given
from hypothesis import strategies as st

from apps.catalog.tests.factories import RipeningPeriodFactory, VarietyFactory
from apps.core.slugs import slugify_uk, transliterate, unique_slug


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # Examples from the plan and the KMU 2010 table.
        ("Ранній Зоряний", "rannii-zorianyi"),
        ("Ювілейний", "yuvileinyi"),
        ("Їжакова Ґронка", "yizhakova-gronka"),
        ("Алушта", "alushta"),
        ("Згорани", "zghorany"),
        ("Розгон", "rozghon"),
        ("Знам'янка", "znamianka"),
        ("Короп'є", "koropie"),
        ("Щербухи", "shcherbukhy"),
        ("Юрій", "yurii"),
        ("Крюківка", "kriukivka"),
        ("Яготин", "yahotyn"),
        ("Костянтин", "kostiantyn"),
        ("Єнакієве", "yenakiieve"),
        ("Гайворон", "haivoron"),
        ("Йосипівка", "yosypivka"),
        ("Стрий", "stryi"),
        ("Олексій", "oleksii"),
        ("Ізмаїл", "izmail"),
        ("Їжакевич", "yizhakevych"),
        ("Кадиївка", "kadyivka"),
        ("Феодосія", "feodosiia"),
        ("Хуст", "khust"),
        ("Цюрупинськ", "tsiurupynsk"),
        ("Чернівці", "chernivtsi"),
        ("Шостка", "shostka"),
        ("Жашків", "zhashkiv"),
        ("Рівне", "rivne"),
        # Breeding codes and mixed text.
        ("12-34 (Тестовий)", "12-34-testovyi"),
        ("Сорт №5 «Перлина»", "sort-no5-perlyna"),
        ("Супер Екстра", "super-ekstra"),
        # Apostrophe variants are dropped inside a word.
        ("М’ята мʼясна", "miata-miasna"),
        ("", ""),
    ],
)
def test_slugify_uk_follows_kmu_2010(text, expected):
    assert slugify_uk(text) == expected


def test_transliterate_keeps_capitalisation_and_other_characters():
    assert transliterate("Щедрий Яр, 2024!") == "Shchedryi Yar, 2024!"


def test_initial_letters_are_spelled_differently_after_a_non_letter():
    assert transliterate("Ян-ян") == "Yan-yan"
    assert transliterate("ян") == "yan"
    assert transliterate("Іван ян") == "Ivan yan"


@given(st.text())
def test_slugify_uk_always_produces_an_ascii_slug(text):
    assert re.fullmatch(r"[a-z0-9_-]*", slugify_uk(text))


def test_unique_slug_returns_base_when_free():
    assert unique_slug("sort", lambda _value: False) == "sort"


def test_unique_slug_adds_first_free_number():
    taken = {"sort", "sort-2"}
    assert unique_slug("sort", taken.__contains__) == "sort-3"


def test_unique_slug_trims_base_to_fit_suffix():
    base = "a" * 10
    slug = unique_slug(base, lambda value: value == base, max_length=10)
    assert slug == "aaaaaaaa-2"
    assert len(slug) == 10


@pytest.mark.django_db
class TestAutoSlugMixin:
    def test_slug_is_generated_from_ukrainian_name(self):
        variety = VarietyFactory(name_uk="Ранній Зоряний", name_en="Early Starry")
        assert variety.slug == "rannii-zorianyi"

    def test_duplicate_names_get_numbered_slugs(self):
        first = VarietyFactory(name_uk="Ювілейний")
        second = VarietyFactory(name_uk="Ювілейний")
        third = VarietyFactory(name_uk="Ювілейний")
        assert [first.slug, second.slug, third.slug] == [
            "yuvileinyi",
            "yuvileinyi-2",
            "yuvileinyi-3",
        ]

    def test_slug_does_not_change_on_rename(self):
        variety = VarietyFactory(name_uk="Старий")
        variety.name_uk = "Новий"
        variety.save()
        variety.refresh_from_db()
        assert variety.slug == "staryi"

    def test_manual_slug_is_kept(self):
        variety = VarietyFactory(name_uk="Ювілейний", slug="my-slug")
        assert variety.slug == "my-slug"

    def test_cleared_slug_is_generated_again_without_clashing_with_itself(self):
        variety = VarietyFactory(name_uk="Ювілейний")
        variety.slug = ""
        variety.save()
        assert variety.slug == "yuvileinyi"

    def test_fallback_when_name_has_no_letters(self):
        assert VarietyFactory(name_uk="!!!").slug == "item"

    def test_slug_ignores_active_language(self, language):
        period = RipeningPeriodFactory(name_uk="Дуже надранній", name_en="Very ultra early")
        assert period.slug == "duzhe-nadrannii"

    def test_slugs_are_unique_per_model(self):
        assert RipeningPeriodFactory(name_uk="Надранній").slug == "nadrannii"
        assert VarietyFactory(name_uk="Надранній").slug == "nadrannii"
