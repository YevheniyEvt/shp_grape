"""State-changing operations of the content app."""

from collections.abc import Iterable

from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.db.models import Max, Model

from apps.content.models import Article, ArticlePhoto, GalleryAlbum, GalleryPhoto


def _append_photos(
    owner: Model, photo_model: type[ArticlePhoto | GalleryPhoto], owner_field: str, files
) -> list:
    # Lock the owner so that parallel uploads do not get the same order numbers.
    type(owner)._default_manager.select_for_update().filter(pk=owner.pk).exists()
    existing = photo_model.objects.filter(**{owner_field: owner})
    last_order = existing.aggregate(last=Max("order"))["last"]
    next_order = 0 if last_order is None else last_order + 1

    created = []
    for offset, file in enumerate(files):
        photo = photo_model(**{owner_field: owner}, image=file, order=next_order + offset)
        photo.full_clean(exclude=[owner_field])
        photo.save()
        created.append(photo)
    return created


@transaction.atomic
def add_album_photos(album: GalleryAlbum, files: Iterable[UploadedFile]) -> list[GalleryPhoto]:
    """Attach uploaded images to an album after its existing photos."""
    return _append_photos(album, GalleryPhoto, "album", files)


@transaction.atomic
def add_article_photos(article: Article, files: Iterable[UploadedFile]) -> list[ArticlePhoto]:
    """Attach uploaded images to an article after its existing photos."""
    return _append_photos(article, ArticlePhoto, "article", files)
