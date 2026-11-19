"""Models of the content app: site settings, news, articles, links, pages and the photo gallery."""

from pathlib import PurePosixPath
from typing import Any

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit
from solo.models import SingletonModel

from apps.catalog.youtube import parse_youtube_id, validate_youtube_url
from apps.core.models import TimeStampedModel
from apps.core.richtext import RichTextField
from apps.core.slugs import AutoSlugMixin

BACKGROUND_MAX_SIZE = 2560


def webp_spec(source: str, width: int, quality: int = 82) -> ImageSpecField:
    """A WebP rendition that fits in `width`×`width` (never upscaled)."""
    return ImageSpecField(
        source=source,
        processors=[ResizeToFit(width, width, upscale=False)],
        format="WEBP",
        options={"quality": quality},
    )


def _file_name(filename: str) -> str:
    return PurePosixPath(filename).name


def background_image_path(instance: SiteSettings, filename: str) -> str:
    """Store site background images in `site/background/<file>`."""
    return f"site/background/{_file_name(filename)}"


def site_file_path(instance: SiteSettings, filename: str) -> str:
    return f"site/{_file_name(filename)}"


class SiteSettings(TimeStampedModel, SingletonModel):
    """Site-wide settings edited in the admin (a single row)."""

    # Identity and home page
    site_name = models.CharField(_("site name"), max_length=100, blank=True)
    tagline = models.CharField(_("tagline"), max_length=200, blank=True)
    welcome = RichTextField(_("welcome text"), help_text=_("Shown on the home page."))
    hero_image = models.ImageField(
        _("home page photo"),
        upload_to=site_file_path,
        blank=True,
        help_text=_("A wide photo for the top of the home page."),
    )
    hero = webp_spec("hero_image", 1920, quality=80)

    # Contacts
    owner_name = models.CharField(_("owner"), max_length=200, blank=True)
    phones = models.TextField(_("phones"), blank=True, help_text=_("One phone number per line."))
    email = models.EmailField(_("email"), blank=True)
    address = models.CharField(_("address"), max_length=300, blank=True)
    map_latitude = models.DecimalField(
        _("map latitude"),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    map_longitude = models.DecimalField(
        _("map longitude"),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    price_list = models.FileField(
        _("price list"),
        upload_to=site_file_path,
        blank=True,
        help_text=_("A file visitors can download (PDF, Word or Excel)."),
    )

    # Links
    facebook_url = models.URLField(_("Facebook"), blank=True)
    instagram_url = models.URLField(_("Instagram"), blank=True)
    youtube_url = models.URLField(_("YouTube channel"), blank=True)
    telegram_url = models.URLField(_("Telegram"), blank=True)
    forum_url = models.URLField(_("forum"), blank=True)

    # Page background
    show_background = models.BooleanField(
        _("show background image"),
        default=True,
        help_text=_("Untick to use a plain background on every page."),
    )
    background_image = models.ImageField(
        _("background image"),
        upload_to=background_image_path,
        blank=True,
        help_text=_(
            "A wide photo (at least 1920 px) shown softly behind the pages. "
            "Leave empty to use the built-in grape illustration."
        ),
    )
    background = webp_spec("background_image", BACKGROUND_MAX_SIZE, quality=78)

    class Meta:
        verbose_name = _("site settings")
        verbose_name_plural = _("site settings")

    def __str__(self) -> str:
        return str(_("Site settings"))

    @property
    def phone_list(self) -> list[str]:
        return [line.strip() for line in self.phones.splitlines() if line.strip()]


class PublishedQuerySet(models.QuerySet):
    def published(self) -> PublishedQuerySet:
        return self.filter(is_published=True, published_at__lte=timezone.localdate())


def publication_cover_path(instance: Publication, filename: str) -> str:
    return f"{instance._meta.model_name}/{_file_name(filename)}"


class Publication(AutoSlugMixin, TimeStampedModel):
    """Base of news and articles: a dated, publishable text with a cover photo."""

    slug_source_field = "title"

    title = models.CharField(_("title"), max_length=200)
    published_at = models.DateField(
        _("publication date"),
        default=timezone.localdate,
        db_index=True,
        help_text=_("A future date hides the entry until that day."),
    )
    cover = models.ImageField(_("cover"), upload_to=publication_cover_path, blank=True)
    cover_card = webp_spec("cover", 800)
    cover_large = webp_spec("cover", 1600)
    body = RichTextField(_("text"))
    is_published = models.BooleanField(_("published"), default=True, db_index=True)

    objects = PublishedQuerySet.as_manager()

    class Meta:
        abstract = True
        ordering = ["-published_at", "-pk"]

    def __str__(self) -> str:
        return self.title


class News(Publication):
    class Meta(Publication.Meta):
        verbose_name = _("news item")
        verbose_name_plural = _("news")


class Article(Publication):
    excerpt = models.TextField(
        _("excerpt"), blank=True, help_text=_("A short summary for the list of articles.")
    )
    author = models.CharField(_("author"), max_length=200, blank=True)

    class Meta(Publication.Meta):
        verbose_name = _("article")
        verbose_name_plural = _("articles")


class OrderedPhoto(models.Model):
    """An ordered photo with a caption, stored size and WebP renditions."""

    image = models.ImageField(_("image"), width_field="width", height_field="height")
    width = models.PositiveIntegerField(_("width"), null=True, blank=True, editable=False)
    height = models.PositiveIntegerField(_("height"), null=True, blank=True, editable=False)
    caption = models.CharField(_("caption"), max_length=255, blank=True)
    order = models.PositiveIntegerField(_("order"), default=0, db_index=True)

    thumb = webp_spec("image", 400)
    medium = webp_spec("image", 1000)
    large = webp_spec("image", 1800)

    class Meta:
        abstract = True
        ordering = ["order", "pk"]

    def __str__(self) -> str:
        return self.caption or _file_name(self.image.name)


def article_photo_path(instance: ArticlePhoto, filename: str) -> str:
    return f"articles/{instance.article.slug}/{_file_name(filename)}"


class ArticlePhoto(OrderedPhoto):
    article = models.ForeignKey(
        Article, verbose_name=_("article"), on_delete=models.CASCADE, related_name="photos"
    )
    image = models.ImageField(
        _("image"), upload_to=article_photo_path, width_field="width", height_field="height"
    )

    class Meta(OrderedPhoto.Meta):
        verbose_name = _("photo")
        verbose_name_plural = _("photos")


class ArticleVideo(models.Model):
    article = models.ForeignKey(
        Article, verbose_name=_("article"), on_delete=models.CASCADE, related_name="videos"
    )
    youtube_url = models.URLField(_("YouTube link"), validators=[validate_youtube_url])
    youtube_id = models.CharField(_("YouTube video id"), max_length=11, editable=False)
    title = models.CharField(_("title"), max_length=200, blank=True)
    order = models.PositiveIntegerField(_("order"), default=0, db_index=True)

    class Meta:
        verbose_name = _("video")
        verbose_name_plural = _("videos")
        ordering = ["order", "pk"]

    def __str__(self) -> str:
        return self.title or self.youtube_url

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.youtube_id = parse_youtube_id(self.youtube_url) or ""
        super().save(*args, **kwargs)


class UsefulLink(models.Model):
    title = models.CharField(_("title"), max_length=200)
    url = models.URLField(_("link"))
    description = models.TextField(_("description"), blank=True)
    order = models.PositiveIntegerField(_("order"), default=0, db_index=True)

    class Meta:
        verbose_name = _("useful link")
        verbose_name_plural = _("useful links")
        ordering = ["order", "pk"]

    def __str__(self) -> str:
        return self.title


class Page(AutoSlugMixin, TimeStampedModel):
    """A standalone text page such as "About us"."""

    ABOUT_SLUG = "about"

    slug_source_field = "title"

    title = models.CharField(_("title"), max_length=200)
    body = RichTextField(_("text"))

    class Meta:
        verbose_name = _("page")
        verbose_name_plural = _("pages")
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title


class GalleryAlbum(AutoSlugMixin, TimeStampedModel):
    """A photo album; its first photo is the cover."""

    slug_source_field = "title"

    title = models.CharField(_("title"), max_length=200)
    description = models.TextField(_("description"), blank=True)
    date = models.DateField(_("date"), default=timezone.localdate)
    order = models.PositiveIntegerField(_("order"), default=0, db_index=True)
    is_published = models.BooleanField(_("published"), default=True, db_index=True)

    class Meta:
        verbose_name = _("album")
        verbose_name_plural = _("albums")
        ordering = ["order", "-date", "-pk"]

    def __str__(self) -> str:
        return self.title


def gallery_photo_path(instance: GalleryPhoto, filename: str) -> str:
    return f"gallery/{instance.album.slug}/{_file_name(filename)}"


class GalleryPhoto(OrderedPhoto):
    album = models.ForeignKey(
        GalleryAlbum, verbose_name=_("album"), on_delete=models.CASCADE, related_name="photos"
    )
    image = models.ImageField(
        _("image"), upload_to=gallery_photo_path, width_field="width", height_field="height"
    )

    class Meta(OrderedPhoto.Meta):
        verbose_name = _("photo")
        verbose_name_plural = _("photos")
