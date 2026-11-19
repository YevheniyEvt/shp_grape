import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from apps.content.models import SiteSettings, background_image_path
from apps.content.serializers import SiteSettingsSerializer

pytestmark = pytest.mark.django_db

URL = reverse("content:site-settings")


def make_image(name: str = "grapes.jpg", size: tuple[int, int] = (40, 20)) -> SimpleUploadedFile:
    buffer = io.BytesIO()
    Image.new("RGB", size, "purple").save(buffer, "JPEG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/jpeg")


def test_default_row_is_created_by_migration():
    settings = SiteSettings.objects.get()
    assert settings.pk == 1
    assert settings.show_background is True
    assert not settings.background_image
    assert str(settings)


def test_background_path_keeps_only_file_name():
    assert background_image_path(SiteSettings(), "../x/photo.jpg") == "site/background/photo.jpg"


def test_api_without_image_returns_null(api_client):
    response = api_client.get(URL)
    assert response.status_code == 200
    assert response.json() == {"show_background": True, "background_image": None}


def test_api_returns_absolute_webp_rendition(api_client):
    settings = SiteSettings.get_solo()
    settings.background_image = make_image()
    settings.save()

    data = api_client.get(URL).json()
    assert data["background_image"].startswith("http://testserver/media/")
    assert data["background_image"].endswith(".webp")


def test_api_reports_disabled_background(api_client):
    settings = SiteSettings.get_solo()
    settings.show_background = False
    settings.save()

    assert api_client.get(URL).json()["show_background"] is False


def test_serializer_without_request_returns_relative_url():
    settings = SiteSettings.get_solo()
    settings.background_image = make_image()
    settings.save()

    url = SiteSettingsSerializer(settings).data["background_image"]
    assert url.startswith("/media/")


@pytest.fixture
def admin_client_logged(client, django_user_model):
    admin = django_user_model.objects.create_superuser("admin", "admin@example.com", "password")
    client.force_login(admin)
    return client


def test_admin_opens_singleton_change_form(admin_client_logged):
    response = admin_client_logged.get(reverse("admin:content_sitesettings_change"))
    assert response.status_code == 200
    assert b"background_image" in response.content


def test_admin_uploads_background_and_shows_preview(admin_client_logged):
    url = reverse("admin:content_sitesettings_change")
    response = admin_client_logged.post(
        url, {"show_background": "on", "background_image": make_image()}
    )
    assert response.status_code == 302

    settings = SiteSettings.get_solo()
    # Storage may append a suffix when another test already saved a file with the same name.
    assert settings.background_image.name.startswith("site/background/grapes")
    assert b".webp" in admin_client_logged.get(url).content
