import pytest

from apps.catalog import demo as catalog_demo
from apps.catalog.tests.factories import VarietyFactory
from apps.content import demo
from apps.content.models import (
    Article,
    ArticleVideo,
    GalleryAlbum,
    GalleryPhoto,
    News,
    Page,
    SiteSettings,
    UsefulLink,
)
from apps.content.selectors import featured_varieties
from apps.content.tests.factories import NewsFactory, UsefulLinkFactory
from apps.core.slugs import slugify_uk

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _small_placeholders(monkeypatch):
    monkeypatch.setattr(catalog_demo, "PLACEHOLDER_SIZE", (120, 90))


def test_frozen_slugs_match_titles():
    for item in (*demo.DEMO_NEWS, *demo.DEMO_ARTICLES):
        assert item.slug == slugify_uk(item.fields["title_uk"])
    assert slugify_uk(demo.DEMO_ALBUM["title_uk"]) == demo.DEMO_ALBUM_SLUG


def test_seed_content_creates_everything():
    report = demo.seed_content()

    assert News.objects.count() == 2
    assert Article.objects.count() == 2
    assert UsefulLink.objects.count() == 3
    assert ArticleVideo.objects.count() == 1
    album = GalleryAlbum.objects.get(slug=demo.DEMO_ALBUM_SLUG)
    assert album.photos.count() == demo.DEMO_ALBUM_PHOTOS
    article = Article.objects.get(slug="yak-posadyty-sadzhanets")
    assert article.photos.count() == 3
    assert article.cover
    assert not News.objects.get(slug="novi-sorty-v-kolektsii").cover

    settings = SiteSettings.get_solo()
    assert settings.phone_list == ["+380 (00) 000-00-00", "+380 (00) 000-00-01"]
    assert settings.hero_image
    assert "settings" in report.created
    assert "Наш виноградник" in Page.objects.get(slug=Page.ABOUT_SLUG).body_uk


def test_seed_content_is_idempotent_and_keeps_edits():
    settings = SiteSettings.get_solo()
    settings.email = "owner@example.org"
    settings.save()
    about = Page.objects.get(slug=Page.ABOUT_SLUG)
    about.body_uk = "<p>Власний текст</p>"
    about.save()

    demo.seed_content()
    again = demo.seed_content()

    assert again.created == []
    assert News.objects.count() == 2
    assert GalleryPhoto.objects.count() == demo.DEMO_ALBUM_PHOTOS
    assert SiteSettings.get_solo().email == "owner@example.org"
    assert Page.objects.get(slug=Page.ABOUT_SLUG).body_uk == "<p>Власний текст</p>"


def test_delete_demo_content_keeps_other_objects():
    demo.seed_content()
    own_news = NewsFactory()
    own_link = UsefulLinkFactory()

    assert demo.delete_demo_content() > 0
    assert list(News.objects.all()) == [own_news]
    assert list(UsefulLink.objects.all()) == [own_link]
    assert not GalleryAlbum.objects.exists()
    assert Page.objects.filter(slug=Page.ABOUT_SLUG).exists()


def test_featured_varieties_respects_the_limit():
    VarietyFactory.create_batch(3, is_featured=True)
    assert len(featured_varieties(limit=2)) == 2
