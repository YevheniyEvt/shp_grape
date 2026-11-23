import io

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from apps.catalog import demo
from apps.catalog.models import Variety
from apps.core.services import ensure_superuser

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _fast_demo(monkeypatch, tmp_path):
    monkeypatch.setattr(demo, "PLACEHOLDER_SIZE", (120, 90))
    for name in ("USERNAME", "EMAIL", "PASSWORD"):
        monkeypatch.delenv(f"DJANGO_SUPERUSER_{name}", raising=False)


def run(*args: str, photos_dir) -> str:
    out = io.StringIO()
    call_command("seed_demo", *args, "--photos-dir", str(photos_dir), stdout=out)
    return out.getvalue()


def test_command_seeds_and_is_idempotent(tmp_path):
    first = run(photos_dir=tmp_path)
    second = run(photos_dir=tmp_path)

    assert "Varieties created: 5" in first
    assert "already present: 5" in second
    assert Variety.objects.count() == len(demo.DEMO_VARIETIES)
    assert "Orders and requests created: 4" in first
    assert "Orders and requests created: 0" in second
    assert "Superuser skipped" in first


def test_reset_recreates_demo_varieties(tmp_path):
    run(photos_dir=tmp_path)
    Variety.objects.filter(slug="bilyi-tuman").update(cutting_available=False)

    output = run("--reset", photos_dir=tmp_path)

    assert "Deleted demo varieties: 5" in output
    assert "Deleted demo orders and requests: 8" in output
    assert "Varieties created: 5" in output
    assert Variety.objects.get(slug="bilyi-tuman").cutting_available is True


def test_command_creates_superuser_from_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("DJANGO_SUPERUSER_USERNAME", "demo-admin")
    monkeypatch.setenv("DJANGO_SUPERUSER_EMAIL", "demo@example.com")
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "secret-password")

    assert "Superuser created: demo-admin" in run(photos_dir=tmp_path)
    assert "Superuser already exists: demo-admin" in run(photos_dir=tmp_path)

    user = get_user_model().objects.get(username="demo-admin")
    assert user.is_superuser
    assert user.is_staff
    assert user.check_password("secret-password")


def test_ensure_superuser_keeps_existing_user(django_user_model):
    django_user_model.objects.create_user(username="admin", password="old")

    assert ensure_superuser("admin", "admin@example.com", "new") is False
    user = django_user_model.objects.get(username="admin")
    assert not user.is_superuser
    assert user.check_password("old")
