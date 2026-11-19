import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from apps.content import services
from apps.content.models import Article, GalleryAlbum, SiteSettings
from apps.content.tests.factories import (
    ArticleFactory,
    ArticlePhotoFactory,
    GalleryAlbumFactory,
    GalleryPhotoFactory,
    NewsFactory,
    PageFactory,
    UsefulLinkFactory,
)

pytestmark = pytest.mark.django_db


def make_image(name: str) -> SimpleUploadedFile:
    buffer = io.BytesIO()
    Image.new("RGB", (20, 10), "green").save(buffer, "JPEG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/jpeg")


@pytest.fixture
def admin_client(client, django_user_model):
    user = django_user_model.objects.create_superuser("admin", "admin@example.com", "password")
    client.force_login(user)
    return client


@pytest.mark.parametrize(
    ("model", "factory"),
    [
        ("news", NewsFactory),
        ("article", ArticleFactory),
        ("usefullink", UsefulLinkFactory),
        ("page", PageFactory),
        ("galleryalbum", GalleryAlbumFactory),
    ],
)
def test_admin_pages_open(admin_client, model, factory):
    obj = factory()
    if model == "galleryalbum":
        GalleryPhotoFactory(album=obj)
    if model == "article":
        ArticlePhotoFactory(article=obj)
        NewsFactory().cover.save("c.jpg", make_image("c.jpg"), save=True)

    for name, args in [("changelist", []), ("add", []), ("change", [obj.pk])]:
        response = admin_client.get(reverse(f"admin:content_{model}_{name}", args=args))
        assert response.status_code == 200, (model, name)


def test_news_changelist_shows_cover(admin_client):
    news = NewsFactory()
    news.cover.save("c.jpg", make_image("c.jpg"), save=True)
    html = admin_client.get(reverse("admin:content_news_changelist")).content.decode()
    assert ".webp" in html


def test_site_settings_admin_shows_previews(admin_client):
    settings = SiteSettings.get_solo()
    settings.hero_image.save("hero.jpg", make_image("hero.jpg"), save=True)

    html = admin_client.get(reverse("admin:content_sitesettings_change")).content.decode()
    assert 'name="phones"' in html
    assert ".webp" in html


def _album_form(album: GalleryAlbum, **extra) -> dict:
    data = {
        "title_uk": album.title_uk,
        "title_en": album.title_en,
        "description_uk": "",
        "description_en": "",
        "date": album.date.isoformat(),
        "is_published": "on",
        "photos-TOTAL_FORMS": "0",
        "photos-INITIAL_FORMS": "0",
        "photos-MIN_NUM_FORMS": "0",
        "photos-MAX_NUM_FORMS": "1000",
    }
    return data | extra


def test_album_bulk_upload(admin_client):
    album = GalleryAlbumFactory()
    GalleryPhotoFactory(album=album, order=5)

    response = admin_client.post(
        reverse("admin:content_galleryalbum_change", args=[album.pk]),
        _album_form(album, upload_photos=[make_image("a.jpg"), make_image("b.jpg")]),
    )

    assert response.status_code == 302
    assert list(album.photos.values_list("order", flat=True)) == [5, 6, 7]


def test_article_bulk_upload(admin_client):
    article = ArticleFactory()
    data = {
        "title_uk": article.title_uk,
        "title_en": article.title_en,
        "author_uk": "",
        "author_en": "",
        "excerpt_uk": "",
        "excerpt_en": "",
        "body_uk": "",
        "body_en": "",
        "published_at": article.published_at.isoformat(),
        "is_published": "on",
        "upload_photos": [make_image("a.jpg")],
    }
    for prefix in ("photos", "videos"):
        data |= {
            f"{prefix}-TOTAL_FORMS": "0",
            f"{prefix}-INITIAL_FORMS": "0",
            f"{prefix}-MIN_NUM_FORMS": "0",
            f"{prefix}-MAX_NUM_FORMS": "1000",
        }

    response = admin_client.post(reverse("admin:content_article_change", args=[article.pk]), data)

    assert response.status_code == 302
    assert Article.objects.get(pk=article.pk).photos.count() == 1


def test_services_append_after_existing_photos():
    album = GalleryAlbumFactory()
    created = services.add_album_photos(album, [make_image("x.jpg"), make_image("y.jpg")])
    assert [photo.order for photo in created] == [0, 1]
    assert created[0].image.name == f"gallery/{album.slug}/x.jpg"

    article = ArticleFactory()
    ArticlePhotoFactory(article=article, order=3)
    created = services.add_article_photos(article, [make_image("z.jpg")])
    assert created[0].order == 4
    assert created[0].image.name.startswith(f"articles/{article.slug}/z")


def test_model_strings():
    album = GalleryAlbumFactory(title_uk="Осінь")
    photo = GalleryPhotoFactory(album=album, caption_uk="")
    assert str(album) == "Осінь"
    assert str(photo).endswith(".jpg")
    assert str(NewsFactory(title_uk="Новина")) == "Новина"
    assert str(UsefulLinkFactory(title_uk="Сайт")) == "Сайт"
    assert str(PageFactory(title_uk="Сторінка")) == "Сторінка"
    video = ArticlePhotoFactory().article.videos.create(youtube_url="https://youtu.be/dQw4w9WgXcQ")
    assert str(video) == "https://youtu.be/dQw4w9WgXcQ"
