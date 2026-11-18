"""State-changing operations of the catalog."""

import hashlib
from collections.abc import Iterable

from django.core.cache import cache
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.db.models import F, Max

from apps.catalog.models import Variety, VarietyPhoto

# One counted view per visitor and variety within this period.
VIEW_THROTTLE_SECONDS = 6 * 60 * 60


def _view_cache_key(variety_id: int, visitor: str) -> str:
    # The visitor identifier (IP address, cookie) is hashed: no personal data in the cache.
    digest = hashlib.sha256(visitor.encode()).hexdigest()[:32]
    return f"catalog:view:{variety_id}:{digest}"


def register_view(variety: Variety, visitor: str) -> bool:
    """
    Count a page view of `variety` once per visitor within `VIEW_THROTTLE_SECONDS`.

    Returns True when the view was counted. The counter is incremented with `F()` in the
    database, so concurrent requests do not lose updates.
    """
    if not cache.add(_view_cache_key(variety.pk, visitor), 1, VIEW_THROTTLE_SECONDS):
        return False
    Variety.objects.filter(pk=variety.pk).update(views_count=F("views_count") + 1)
    return True


@transaction.atomic
def add_photos(variety: Variety, files: Iterable[UploadedFile]) -> list[VarietyPhoto]:
    """
    Attach uploaded images to `variety` after its existing photos.

    The first photo becomes the main one when the variety has none yet.
    """
    # Lock the variety so that parallel uploads do not get the same order numbers.
    Variety.objects.select_for_update().filter(pk=variety.pk).exists()
    photos = variety.photos.all()
    last_order = photos.aggregate(last=Max("order"))["last"]
    next_order = 0 if last_order is None else last_order + 1
    needs_main = not photos.filter(is_main=True).exists()

    created = []
    for offset, file in enumerate(files):
        photo = VarietyPhoto(
            variety=variety,
            image=file,
            order=next_order + offset,
            is_main=needs_main and offset == 0,
        )
        photo.full_clean(exclude=["variety"])
        photo.save()
        created.append(photo)
    return created
