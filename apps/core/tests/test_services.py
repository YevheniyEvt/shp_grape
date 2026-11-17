from unittest import mock

import pytest
from django.db import DatabaseError

from apps.core import services
from apps.core.version import get_project_version


@pytest.mark.django_db
def test_check_health_reports_ok_when_database_answers():
    health = services.check_health()

    assert health.is_healthy
    assert health.database == "ok"
    assert health.version == get_project_version()


def test_check_health_reports_error_when_database_fails():
    with mock.patch.object(services.connection, "cursor", side_effect=DatabaseError("down")):
        health = services.check_health()

    assert not health.is_healthy
    assert health.status == "error"
    assert health.database == "unavailable"


def test_get_languages_lists_configured_languages_with_native_names(settings):
    settings.LANGUAGE_CODE = "uk"
    settings.LANGUAGES = [("uk", "Ukrainian"), ("en", "English")]
    settings.LANGUAGE_NATIVE_NAMES = {"uk": "Українська", "en": "English"}

    assert services.get_languages() == [
        {"code": "uk", "name": "Українська", "is_default": True},
        {"code": "en", "name": "English", "is_default": False},
    ]


def test_get_languages_falls_back_to_configured_name(settings):
    settings.LANGUAGES = [("uk", "Ukrainian"), ("de", "German")]
    settings.LANGUAGE_NATIVE_NAMES = {"uk": "Українська"}

    names = [language["name"] for language in services.get_languages()]

    assert names == ["Українська", "German"]


@pytest.mark.parametrize(
    ("code", "expected"),
    [("uk", True), ("en", True), ("de", False), ("", False), ("UK", False)],
)
def test_is_supported_language(code, expected):
    assert services.is_supported_language(code) is expected
