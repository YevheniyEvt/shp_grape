"""Business logic of the core app: health checks and language metadata."""

from dataclasses import dataclass

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import DatabaseError, connection

from apps.core.version import get_project_version


@dataclass(frozen=True)
class HealthStatus:
    """Result of a service health check."""

    status: str
    database: str
    version: str

    @property
    def is_healthy(self) -> bool:
        return self.status == "ok"


def check_health() -> HealthStatus:
    """Check that the database answers a trivial query."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        return HealthStatus(status="error", database="unavailable", version=get_project_version())
    return HealthStatus(status="ok", database="ok", version=get_project_version())


def get_languages() -> list[dict[str, str | bool]]:
    """Return configured site languages with their native names, default first."""
    native_names: dict[str, str] = getattr(settings, "LANGUAGE_NATIVE_NAMES", {})
    return [
        {
            "code": code,
            "name": native_names.get(code, str(name)),
            "is_default": code == settings.LANGUAGE_CODE,
        }
        for code, name in settings.LANGUAGES
    ]


def is_supported_language(code: str) -> bool:
    """Return True if `code` is one of the configured site languages."""
    return code in {lang_code for lang_code, _name in settings.LANGUAGES}


def ensure_superuser(username: str, email: str, password: str) -> bool:
    """
    Create a superuser unless a user with this username exists.

    Returns True when a user was created. Used by `seed_demo` with the `DJANGO_SUPERUSER_*`
    variables, so a fresh demo database can be opened in the admin right away.
    """
    user_model = get_user_model()
    if user_model._default_manager.filter(**{user_model.USERNAME_FIELD: username}).exists():
        return False
    user_model._default_manager.create_superuser(username=username, email=email, password=password)
    return True
