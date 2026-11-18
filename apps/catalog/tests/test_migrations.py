"""Tests of the data migration with default reference-list values."""

import importlib

import pytest
from django.apps import apps

from apps.catalog.models import BerryColor, GrowthVigor, PulpConsistency, RipeningPeriod, Taste
from apps.catalog.tests.factories import VarietyFactory
from apps.core.slugs import slugify_uk

pytestmark = pytest.mark.django_db

migration = importlib.import_module("apps.catalog.migrations.0003_default_dictionaries")

MODELS = {
    "RipeningPeriod": RipeningPeriod,
    "BerryColor": BerryColor,
    "PulpConsistency": PulpConsistency,
    "Taste": Taste,
    "GrowthVigor": GrowthVigor,
}


@pytest.mark.parametrize("model_name", list(migration.DEFAULTS))
def test_defaults_are_created_in_both_languages_and_order(model_name):
    rows = migration.DEFAULTS[model_name]
    model = MODELS[model_name]

    created = list(model.objects.filter(slug__in=[slug for slug, _uk, _en in rows]))

    assert [(item.slug, item.name_uk, item.name_en) for item in created] == rows
    assert [item.order for item in created] == list(range(1, len(rows) + 1))


@pytest.mark.parametrize(
    ("slug", "name_uk"),
    [(slug, name_uk) for rows in migration.DEFAULTS.values() for slug, name_uk, _en in rows],
)
def test_frozen_slugs_match_the_slug_generator(slug, name_uk):
    assert slugify_uk(name_uk) == slug


def test_rerun_keeps_admin_edits_and_creates_no_duplicates():
    early = RipeningPeriod.objects.get(slug="rannii")
    early.name_uk = "Ранній (змінено)"
    early.save()
    count = RipeningPeriod.objects.count()

    migration.create_defaults(apps, None)

    assert RipeningPeriod.objects.count() == count
    early.refresh_from_db()
    assert early.name_uk == "Ранній (змінено)"


def test_reverse_keeps_values_used_by_varieties():
    used = RipeningPeriod.objects.get(slug="rannii")
    VarietyFactory(ripening=used)

    migration.remove_unused_defaults(apps, None)

    assert list(RipeningPeriod.objects.values_list("slug", flat=True)) == ["rannii"]
    assert not BerryColor.objects.exists()
