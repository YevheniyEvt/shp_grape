"""Shared pytest fixtures for all apps."""

from collections.abc import Iterator

import pytest
from django.conf import settings
from django.utils import translation
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def _default_language() -> Iterator[None]:
    """Start every test in the default language: requests activate languages for the thread."""
    translation.activate(settings.LANGUAGE_CODE)
    yield
    translation.activate(settings.LANGUAGE_CODE)


@pytest.fixture
def api_client() -> APIClient:
    """DRF test client, unauthenticated."""
    return APIClient()


@pytest.fixture
def user(django_user_model):
    """A regular active user."""
    return django_user_model.objects.create_user(username="user", password="password")


@pytest.fixture(params=["uk", "en"])
def language(request) -> Iterator[str]:
    """Run a test once per site language with that language active."""
    with translation.override(request.param):
        yield request.param
