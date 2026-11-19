import datetime
from decimal import Decimal

import pytest
from django.core.files.base import ContentFile
from django.urls import reverse
from django.utils import timezone

from apps.catalog.tests.factories import VarietyFactory, VarietyPhotoFactory
from apps.content.models import Page, SiteSettings
from apps.content.tests.factories import (
    ArticleFactory,
    ArticlePhotoFactory,
    ArticleVideoFactory,
    GalleryAlbumFactory,
    GalleryPhotoFactory,
    NewsFactory,
    UsefulLinkFactory,
)

pytestmark = pytest.mark.django_db

TODAY = timezone.localdate()
TOMORROW = TODAY + datetime.timedelta(days=1)


def url(name: str, *args) -> str:
    return reverse(f"content:{name}", args=args)


# --- settings ------------------------------------------------------------------------------


def test_settings_defaults_in_both_languages(api_client):
    uk = api_client.get(url("site-settings")).json()
    en = api_client.get(url("site-settings"), HTTP_ACCEPT_LANGUAGE="en").json()

    assert uk["site_name"] == "Виноградник"
    assert en["site_name"] == "Vineyard"
    assert uk["phones"] == []
    assert uk["map"] is None
    assert uk["price_list"] is None
    assert uk["social"] == dict.fromkeys(
        ["facebook", "instagram", "youtube", "telegram", "forum"], ""
    )


def test_settings_contacts(api_client):
    settings = SiteSettings.get_solo()
    settings.phones = "+380 (00) 000-00-00\n\n  +380 (00) 000-00-01  \n"
    settings.email = "info@example.com"
    settings.map_latitude = Decimal("49.5")
    settings.map_longitude = Decimal("31.25")
    settings.youtube_url = "https://youtube.com/@demo"
    settings.price_list.save("prices.pdf", ContentFile(b"%PDF"), save=False)
    settings.save()

    data = api_client.get(url("site-settings")).json()

    assert data["phones"] == ["+380 (00) 000-00-00", "+380 (00) 000-00-01"]
    assert data["map"] == {"latitude": 49.5, "longitude": 31.25}
    assert data["price_list"].startswith("http://testserver/media/site/prices")
    assert data["social"]["youtube"] == "https://youtube.com/@demo"


# --- news and articles ---------------------------------------------------------------------


def test_news_list_hides_unpublished_and_future_items(api_client):
    old = NewsFactory(published_at=TODAY - datetime.timedelta(days=3))
    new = NewsFactory(published_at=TODAY)
    NewsFactory(is_published=False)
    NewsFactory(published_at=TOMORROW)

    data = api_client.get(url("news-list")).json()

    assert data["count"] == 2
    assert [item["slug"] for item in data["results"]] == [new.slug, old.slug]
    assert data["results"][0]["cover"] is None


def test_news_detail_and_404(api_client):
    news = NewsFactory()
    hidden = NewsFactory(published_at=TOMORROW)

    data = api_client.get(url("news-detail", news.slug), HTTP_ACCEPT_LANGUAGE="en").json()
    assert data["title"] == news.title_en
    assert data["body"] == "<p>Текст новини</p>"  # fallback to Ukrainian
    assert api_client.get(url("news-detail", hidden.slug)).status_code == 404


def test_news_cover_renditions(api_client):
    news = NewsFactory()
    news.cover.save("cover.jpg", ArticlePhotoFactory.build().image.file, save=True)

    cover = api_client.get(url("news-list")).json()["results"][0]["cover"]
    assert cover["card"].endswith(".webp")
    assert cover["large"].endswith(".webp")
    assert cover["width"] == 40


def test_article_list_and_detail_with_photos_and_videos(api_client, django_assert_max_num_queries):
    article = ArticleFactory(author_uk="О. Демченко")
    ArticlePhotoFactory(article=article, caption_uk="Гроно")
    ArticlePhotoFactory(article=article)
    ArticleVideoFactory(article=article, title_uk="Огляд")

    listing = api_client.get(url("article-list")).json()["results"][0]
    assert listing["excerpt"] == "Короткий опис"
    assert listing["author"] == "О. Демченко"

    with django_assert_max_num_queries(5):
        data = api_client.get(url("article-detail", article.slug)).json()
    assert [photo["alt"] for photo in data["photos"]] == ["Гроно", article.title_uk]
    assert data["photos"][0]["thumb"].endswith(".webp")
    assert data["videos"][0]["youtube_id"] == "dQw4w9WgXcQ"


# --- links and pages -----------------------------------------------------------------------


def test_links_in_order(api_client):
    second = UsefulLinkFactory(order=2)
    first = UsefulLinkFactory(order=1, description_uk="Опис")

    data = api_client.get(url("link-list")).json()
    assert [item["id"] for item in data] == [first.id, second.id]
    assert data[0]["description"] == "Опис"


def test_about_page_from_migration(api_client):
    data = api_client.get(url("page-detail", Page.ABOUT_SLUG), HTTP_ACCEPT_LANGUAGE="en").json()
    assert data["title"] == "About us"
    assert api_client.get(url("page-detail", "missing")).status_code == 404


# --- gallery -------------------------------------------------------------------------------


def test_albums_skip_empty_and_unpublished(api_client):
    album = GalleryAlbumFactory()
    GalleryPhotoFactory(album=album, order=1, caption_uk="Перше")
    GalleryPhotoFactory(album=album, order=2)
    GalleryAlbumFactory()  # empty
    GalleryPhotoFactory(album=GalleryAlbumFactory(is_published=False))

    data = api_client.get(url("album-list")).json()

    assert [item["slug"] for item in data] == [album.slug]
    assert data[0]["photo_count"] == 2
    assert data[0]["cover"]["alt"] == "Перше"


def test_album_detail(api_client):
    album = GalleryAlbumFactory()
    GalleryPhotoFactory(album=album, order=2)
    first = GalleryPhotoFactory(album=album, order=1)

    data = api_client.get(url("album-detail", album.slug)).json()
    assert [photo["id"] for photo in data["photos"]] == [first.id, data["photos"][1]["id"]]
    assert data["photos"][1]["alt"] == album.title_uk
    assert data["photo_count"] == 2

    hidden = GalleryAlbumFactory(is_published=False)
    assert api_client.get(url("album-detail", hidden.slug)).status_code == 404


def test_photo_feed_combines_albums_and_varieties(api_client):
    album_photo = GalleryPhotoFactory()
    variety = VarietyFactory()
    variety_photo = VarietyPhotoFactory(variety=variety, alt_uk="")
    VarietyPhotoFactory(variety=VarietyFactory(is_published=False))
    GalleryPhotoFactory(album=GalleryAlbumFactory(is_published=False))

    data = api_client.get(url("photo-feed")).json()

    assert data["count"] == 2
    assert data["next_page"] is None
    assert [item["id"] for item in data["results"]] == [
        f"album-{album_photo.id}",
        f"variety-{variety_photo.id}",
    ]
    assert data["results"][0]["source"] == {
        "kind": "album",
        "slug": album_photo.album.slug,
        "title": album_photo.album.title,
    }
    assert data["results"][1]["alt"] == variety.name
    assert data["results"][1]["source"]["kind"] == "variety"


def test_photo_feed_pagination(api_client, monkeypatch):
    from apps.content import views

    monkeypatch.setattr(views, "FEED_PAGE_SIZE", 2)
    photos = [GalleryPhotoFactory() for _ in range(3)]

    first = api_client.get(url("photo-feed")).json()
    second = api_client.get(url("photo-feed"), {"page": first["next_page"]}).json()
    beyond = api_client.get(url("photo-feed"), {"page": 9}).json()
    invalid = api_client.get(url("photo-feed"), {"page": "x"}).json()

    assert first["next_page"] == 2
    assert [item["id"] for item in first["results"] + second["results"]] == [
        f"album-{photo.id}" for photo in reversed(photos)
    ]
    assert second["next_page"] is None
    assert beyond["results"] == []
    assert invalid["results"] == first["results"]


# --- home ----------------------------------------------------------------------------------


def test_home_aggregate(api_client):
    NewsFactory(published_at=TODAY - datetime.timedelta(days=1))
    latest = NewsFactory()
    articles = [ArticleFactory(published_at=TODAY - datetime.timedelta(days=n)) for n in range(4)]
    featured = VarietyFactory(is_featured=True)
    others = [VarietyFactory() for _ in range(4)]
    VarietyFactory(is_featured=True, is_published=False)

    settings = SiteSettings.get_solo()
    settings.welcome_uk = "<p>Вітаємо</p>"
    settings.hero_image.save("hero.jpg", ArticlePhotoFactory.build().image.file, save=True)

    data = api_client.get(url("home")).json()

    assert data["welcome"] == "<p>Вітаємо</p>"
    assert data["hero_image"].endswith(".webp")
    assert data["latest_news"]["slug"] == latest.slug
    assert [item["slug"] for item in data["latest_articles"]] == [a.slug for a in articles[:3]]
    slugs = [item["slug"] for item in data["featured_varieties"]]
    assert slugs[0] == featured.slug
    assert len(slugs) == 4
    assert set(slugs[1:]) <= {variety.slug for variety in others}


def test_home_without_content(api_client):
    data = api_client.get(url("home")).json()
    assert data == {
        "welcome": "",
        "hero_image": None,
        "latest_news": None,
        "featured_varieties": [],
        "latest_articles": [],
    }
