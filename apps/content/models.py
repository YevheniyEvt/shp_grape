"""Models of the content app."""

from pathlib import PurePosixPath

from django.db import models
from django.utils.translation import gettext_lazy as _
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit
from solo.models import SingletonModel

from apps.core.models import TimeStampedModel

BACKGROUND_MAX_SIZE = 2560


def background_image_path(instance: SiteSettings, filename: str) -> str:
    """Store site background images in `site/background/<file>`."""
    return f"site/background/{PurePosixPath(filename).name}"


class SiteSettings(TimeStampedModel, SingletonModel):
    """
    Site-wide settings edited in the admin (a single row).

    Holds only the page background for now; contacts, texts and the price list are added
    in stage 5.
    """

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
    background = ImageSpecField(
        source="background_image",
        processors=[ResizeToFit(BACKGROUND_MAX_SIZE, BACKGROUND_MAX_SIZE, upscale=False)],
        format="WEBP",
        options={"quality": 78},
    )

    class Meta:
        verbose_name = _("site settings")
        verbose_name_plural = _("site settings")

    def __str__(self) -> str:
        return str(_("Site settings"))
