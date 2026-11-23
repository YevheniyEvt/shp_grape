"""Fixtures of the orders tests."""

from collections.abc import Iterator
from decimal import Decimal

import pytest
from django.core.cache import cache

from apps.catalog.models import Variety
from apps.catalog.tests.factories import VarietyFactory
from apps.content.models import SiteSettings

OWNER_EMAIL = "owner@example.com"


@pytest.fixture(autouse=True)
def _clear_cache() -> Iterator[None]:
    """Throttling counters live in the cache: every test starts with clean limits."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def owner_email(db) -> str:
    settings = SiteSettings.get_solo()
    settings.email = OWNER_EMAIL
    settings.save()
    return OWNER_EMAIL


@pytest.fixture
def variety(db) -> Variety:
    """A variety with both cuttings and saplings in stock."""
    return VarietyFactory(
        slug="rubin",
        name_uk="Рубін",
        name_en="Ruby",
        cutting_price=Decimal("30.00"),
        cutting_available=True,
        sapling_price=Decimal("120.00"),
        sapling_available=True,
    )


@pytest.fixture
def sold_out(db) -> Variety:
    """A variety with a price but nothing in stock."""
    return VarietyFactory(
        slug="sapfir",
        name_uk="Сапфір",
        name_en="Sapphire",
        cutting_price=Decimal("40.00"),
        cutting_available=False,
        sapling_price=None,
        sapling_available=True,
    )
