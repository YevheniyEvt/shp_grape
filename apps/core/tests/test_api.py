from unittest import mock

import pytest
from django.urls import reverse

from apps.core.services import HealthStatus
from apps.core.version import get_project_version


@pytest.mark.django_db
def test_health_returns_ok_and_version(api_client):
    response = api_client.get(reverse("core:health"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok", "version": get_project_version()}


def test_health_returns_503_when_unhealthy(api_client):
    unhealthy = HealthStatus(status="error", database="unavailable", version="0.0.0")
    with mock.patch("apps.core.views.services.check_health", return_value=unhealthy):
        response = api_client.get(reverse("core:health"))

    assert response.status_code == 503
    assert response.json()["database"] == "unavailable"


def test_languages_endpoint_lists_site_languages(api_client):
    response = api_client.get(reverse("core:languages"))

    assert response.status_code == 200
    assert [language["code"] for language in response.json()] == ["uk", "en"]
    assert response.json()[0]["is_default"] is True


@pytest.mark.parametrize(
    ("accept_language", "expected_detail"),
    [
        ("uk", 'Метод "POST" не дозволений.'),
        ("en", 'Method "POST" not allowed.'),
    ],
)
def test_api_errors_follow_accept_language(api_client, accept_language, expected_detail):
    response = api_client.post(reverse("core:health"), HTTP_ACCEPT_LANGUAGE=accept_language)

    assert response.status_code == 405
    assert response.json()["detail"] == expected_detail


def test_translation_catalog_rejects_unknown_language(api_client):
    response = api_client.get(reverse("core:translation-catalog", kwargs={"lang": "de"}))

    assert response.status_code == 404


@pytest.mark.parametrize("lang", ["uk", "en"])
def test_translation_catalog_returns_gettext_payload(api_client, lang):
    response = api_client.get(reverse("core:translation-catalog", kwargs={"lang": lang}))

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"catalog", "formats", "plural"}


def test_translation_catalog_contains_ukrainian_frontend_strings(api_client):
    response = api_client.get(reverse("core:translation-catalog", kwargs={"lang": "uk"}))

    catalog = response.json()["catalog"]
    assert catalog["Catalog"] == "Каталог"
    # The plural formula of the Ukrainian catalog is shipped for nt() on the frontend.
    assert isinstance(response.json()["plural"], str)


def test_translation_catalog_excludes_django_admin_strings(api_client):
    response = api_client.get(reverse("core:translation-catalog", kwargs={"lang": "uk"}))

    # "Choose a Date" comes from django.contrib.admin's djangojs catalog.
    assert "Choose a Date" not in response.json()["catalog"]


def test_schema_and_docs_are_served(api_client):
    assert api_client.get(reverse("schema")).status_code == 200
    assert api_client.get(reverse("swagger-ui")).status_code == 200
