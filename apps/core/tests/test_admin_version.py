import pytest
from django.urls import reverse
from django.utils import translation

from apps.core.version import get_project_version

pytestmark = pytest.mark.django_db


def test_login_page_shows_project_version(client):
    response = client.get(reverse("admin:login"))
    assert response.status_code == 200
    html = response.content.decode()
    assert 'id="site-version"' in html
    assert get_project_version() in html


def test_admin_index_shows_translated_version_label(client, django_user_model):
    admin = django_user_model.objects.create_superuser("admin", "admin@example.com", "password")
    client.force_login(admin)

    html = client.get(reverse("admin:index")).content.decode()
    # The admin is always rendered in Ukrainian (AdminLanguageMiddleware).
    with translation.override("uk"):
        label = translation.gettext("Version %(version)s") % {"version": get_project_version()}
    assert label in html
    assert label != f"Version {get_project_version()}"
