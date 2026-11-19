"""Read-only queries of the content app."""

from dataclasses import dataclass
from typing import Literal

from django.db.models import CharField, Count, Prefetch, QuerySet, Value

from apps.catalog.models import Variety, VarietyPhoto
from apps.catalog.selectors import variety_list
from apps.content.models import (
    Article,
    GalleryAlbum,
    GalleryPhoto,
    News,
    Page,
    UsefulLink,
)

HOME_FEATURED_VARIETIES = 4
HOME_LATEST_ARTICLES = 3


def news_list() -> QuerySet[News]:
    return News.objects.published()


def article_list() -> QuerySet[Article]:
    return Article.objects.published()


def article_detail_queryset() -> QuerySet[Article]:
    return article_list().prefetch_related("photos", "videos")


def useful_links() -> QuerySet[UsefulLink]:
    return UsefulLink.objects.all()


def pages() -> QuerySet[Page]:
    return Page.objects.all()


def _cover_prefetch() -> Prefetch:
    return Prefetch(
        "photos", queryset=GalleryPhoto.objects.order_by("order", "pk"), to_attr="ordered_photos"
    )


def album_list() -> QuerySet[GalleryAlbum]:
    """Published albums that have photos, with the photo count and the cover photo."""
    return (
        GalleryAlbum.objects.filter(is_published=True)
        .annotate(photo_count=Count("photos"))
        .filter(photo_count__gt=0)
        .prefetch_related(_cover_prefetch())
    )


def album_detail_queryset() -> QuerySet[GalleryAlbum]:
    return GalleryAlbum.objects.filter(is_published=True).prefetch_related(_cover_prefetch())


def featured_varieties(limit: int = HOME_FEATURED_VARIETIES) -> list[Variety]:
    """Featured varieties for the home page; newest varieties fill the rest."""
    featured = list(variety_list().filter(is_featured=True).order_by("?")[:limit])
    if len(featured) < limit:
        taken = [variety.pk for variety in featured]
        featured += list(
            variety_list().exclude(pk__in=taken).order_by("-created_at")[: limit - len(featured)]
        )
    return featured


@dataclass(frozen=True)
class HomeContent:
    latest_news: News | None
    featured_varieties: list[Variety]
    latest_articles: list[Article]


def home_content() -> HomeContent:
    return HomeContent(
        latest_news=news_list().first(),
        featured_varieties=featured_varieties(),
        latest_articles=list(article_list()[:HOME_LATEST_ARTICLES]),
    )


# ---------------------------------------------------------------------------
# Photo feed: album photos and variety photos in one paginated stream
# ---------------------------------------------------------------------------

PhotoKind = Literal["album", "variety"]


@dataclass(frozen=True)
class FeedPhoto:
    kind: PhotoKind
    photo: GalleryPhoto | VarietyPhoto


def photo_feed_refs() -> QuerySet:
    """
    `(kind, id)` rows of all published photos, album photos first, newest first.

    A UNION of two tables keeps pagination in the database; `load_feed_photos` turns
    one page of rows into photo objects.
    """
    album = (
        GalleryPhoto.objects.filter(album__is_published=True)
        .annotate(kind=Value("album", output_field=CharField()))
        .values_list("kind", "id")
    )
    variety = (
        VarietyPhoto.objects.filter(variety__is_published=True)
        .annotate(kind=Value("variety", output_field=CharField()))
        .values_list("kind", "id")
    )
    return album.union(variety, all=True).order_by("kind", "-id")


def load_feed_photos(refs: list[tuple[str, int]]) -> list[FeedPhoto]:
    """Photo objects for feed rows, in the same order."""
    ids: dict[str, list[int]] = {"album": [], "variety": []}
    for kind, pk in refs:
        ids[kind].append(pk)
    found: dict[tuple[str, int], GalleryPhoto | VarietyPhoto] = {}
    for photo in GalleryPhoto.objects.filter(pk__in=ids["album"]).select_related("album"):
        found[("album", photo.pk)] = photo
    for photo in VarietyPhoto.objects.filter(pk__in=ids["variety"]).select_related("variety"):
        found[("variety", photo.pk)] = photo
    return [
        FeedPhoto(kind=kind, photo=found[(kind, pk)])  # type: ignore[arg-type]
        for kind, pk in refs
        if (kind, pk) in found
    ]
