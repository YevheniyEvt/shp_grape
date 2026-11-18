"""Models of the catalog app: grape varieties, their photos and videos, and reference lists."""

from pathlib import PurePosixPath
from typing import Any

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import F, Q
from django.utils.translation import gettext_lazy as _
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit

from apps.catalog.alphabet import first_letter
from apps.catalog.youtube import parse_youtube_id, validate_youtube_url
from apps.core.models import SlugNaturalKeyManager, TimeStampedModel
from apps.core.richtext import RichTextField
from apps.core.slugs import AutoSlugMixin

# Pairs of fields that describe a range; `min` must not exceed `max`.
VARIETY_RANGES: tuple[str, ...] = (
    "bunch_weight",
    "berry_weight",
    "berry_size",
    "disease_susceptibility",
)


class Dictionary(AutoSlugMixin, models.Model):
    """Base model of a reference list (ripening period, berry colour, ...)."""

    name = models.CharField(_("name"), max_length=100)
    order = models.PositiveIntegerField(_("order"), default=0, db_index=True)

    objects = SlugNaturalKeyManager()

    class Meta:
        abstract = True
        ordering = ["order", "name"]

    def __str__(self) -> str:
        return self.name

    def natural_key(self) -> tuple[str]:
        return (self.slug,)


class RipeningPeriod(Dictionary):
    class Meta(Dictionary.Meta):
        verbose_name = _("ripening period")
        verbose_name_plural = _("ripening periods")


class BerryColor(Dictionary):
    class Meta(Dictionary.Meta):
        verbose_name = _("berry colour")
        verbose_name_plural = _("berry colours")


class PulpConsistency(Dictionary):
    class Meta(Dictionary.Meta):
        verbose_name = _("pulp consistency")
        verbose_name_plural = _("pulp consistencies")


class Taste(Dictionary):
    class Meta(Dictionary.Meta):
        verbose_name = _("taste")
        verbose_name_plural = _("tastes")


class GrowthVigor(Dictionary):
    class Meta(Dictionary.Meta):
        verbose_name = _("growth vigour")
        verbose_name_plural = _("growth vigour")


def _dictionary_fk(model: type[Dictionary], verbose_name: Any) -> models.ForeignKey:
    return models.ForeignKey(
        model,
        verbose_name=verbose_name,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="varieties",
    )


def _range_field(verbose_name: Any, max_digits: int, decimal_places: int) -> models.DecimalField:
    return models.DecimalField(
        verbose_name,
        max_digits=max_digits,
        decimal_places=decimal_places,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )


def _price_field(verbose_name: Any) -> models.DecimalField:
    return models.DecimalField(
        verbose_name,
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text=_("In UAH."),
    )


class Variety(AutoSlugMixin, TimeStampedModel):
    """A grape variety: characteristics, description, prices and availability."""

    name = models.CharField(_("name"), max_length=200)
    alt_names = models.CharField(
        _("alternative names"),
        max_length=500,
        blank=True,
        help_text=_("Other spellings and synonyms, separated by commas. Used by the search."),
    )
    author = models.CharField(_("breeder"), max_length=200, blank=True)

    ripening = _dictionary_fk(RipeningPeriod, _("ripening period"))
    berry_color = _dictionary_fk(BerryColor, _("berry colour"))
    pulp = _dictionary_fk(PulpConsistency, _("pulp consistency"))
    taste = _dictionary_fk(Taste, _("taste"))
    vigor = _dictionary_fk(GrowthVigor, _("growth vigour"))

    bunch_weight_min = _range_field(_("bunch weight from, kg"), 5, 2)
    bunch_weight_max = _range_field(_("bunch weight to, kg"), 5, 2)
    berry_weight_min = _range_field(_("berry weight from, g"), 5, 1)
    berry_weight_max = _range_field(_("berry weight to, g"), 5, 1)
    berry_size_min = _range_field(_("berry size from, mm"), 5, 1)
    berry_size_max = _range_field(_("berry size to, mm"), 5, 1)
    disease_susceptibility_min = _range_field(_("disease susceptibility from, points"), 3, 1)
    disease_susceptibility_max = _range_field(_("disease susceptibility to, points"), 3, 1)
    frost_resistance = models.SmallIntegerField(
        _("frost resistance, °C"),
        null=True,
        blank=True,
        help_text=_("Lowest tolerated temperature, e.g. -23."),
    )

    description = RichTextField(_("description"))

    cutting_price = _price_field(_("cutting price"))
    cutting_available = models.BooleanField(_("cuttings available"), default=False)
    sapling_price = _price_field(_("sapling price"))
    sapling_available = models.BooleanField(_("saplings available"), default=False)

    is_featured = models.BooleanField(
        _("featured"), default=False, help_text=_("Shown on the home page.")
    )
    is_published = models.BooleanField(_("published"), default=True, db_index=True)
    views_count = models.PositiveIntegerField(_("views"), default=0, editable=False)
    # Navigation letter of the name; translated, so every language has its own column.
    first_letter = models.CharField(_("first letter"), max_length=1, blank=True, editable=False)

    objects = SlugNaturalKeyManager()

    class Meta:
        verbose_name = _("variety")
        verbose_name_plural = _("varieties")
        ordering = ["name"]
        indexes = [
            *(
                GinIndex(
                    fields=[f"{field}_{code}"],
                    opclasses=["gin_trgm_ops"],
                    name=f"catalog_var_{field}_{code}_trgm",
                )
                for field in ("name", "alt_names")
                for code, _name in settings.LANGUAGES
            ),
            *(
                models.Index(fields=[f"first_letter_{code}"], name=f"catalog_var_letter_{code}")
                for code, _name in settings.LANGUAGES
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(**{f"{field}_min__isnull": True})
                | Q(**{f"{field}_max__isnull": True})
                | Q(**{f"{field}_min__lte": F(f"{field}_max")}),
                name=f"catalog_var_{field}_range",
            )
            for field in VARIETY_RANGES
        ]

    def __str__(self) -> str:
        return self.name

    def natural_key(self) -> tuple[str]:
        return (self.slug,)

    def clean(self) -> None:
        super().clean()
        errors = {}
        for field in VARIETY_RANGES:
            low = getattr(self, f"{field}_min")
            high = getattr(self, f"{field}_max")
            if low is not None and high is not None and low > high:
                errors[f"{field}_max"] = _("The upper bound must not be less than the lower one.")
        if errors:
            raise ValidationError(errors)

    def update_first_letters(self) -> None:
        """Set the navigation letter for every language from the name shown in that language."""
        default_name = getattr(self, f"name_{settings.LANGUAGE_CODE}", None) or self.name
        for code, _name in settings.LANGUAGES:
            name = getattr(self, f"name_{code}", None) or default_name
            setattr(self, f"first_letter_{code}", first_letter(name))

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.update_first_letters()
        update_fields = kwargs.get("update_fields")
        if update_fields is not None and any(field.startswith("name") for field in update_fields):
            kwargs["update_fields"] = {
                *update_fields,
                *(f"first_letter_{code}" for code, _name in settings.LANGUAGES),
            }
        super().save(*args, **kwargs)


def variety_photo_path(instance: VarietyPhoto, filename: str) -> str:
    """Store photos in a folder per variety: `varieties/<slug>/<file>`."""
    return f"varieties/{instance.variety.slug}/{PurePosixPath(filename).name}"


def _webp_spec(width: int) -> ImageSpecField:
    return ImageSpecField(
        source="image",
        processors=[ResizeToFit(width, width, upscale=False)],
        format="WEBP",
        options={"quality": 82},
    )


class VarietyPhoto(models.Model):
    """A photo of a variety with WebP renditions for cards, the page and the lightbox."""

    variety = models.ForeignKey(
        Variety, verbose_name=_("variety"), on_delete=models.CASCADE, related_name="photos"
    )
    image = models.ImageField(
        _("image"), upload_to=variety_photo_path, width_field="width", height_field="height"
    )
    width = models.PositiveIntegerField(_("width"), null=True, blank=True, editable=False)
    height = models.PositiveIntegerField(_("height"), null=True, blank=True, editable=False)
    alt = models.CharField(
        _("alternative text"),
        max_length=255,
        blank=True,
        help_text=_("Describes the photo for screen readers and search engines."),
    )
    order = models.PositiveIntegerField(_("order"), default=0, db_index=True)
    is_main = models.BooleanField(
        _("main photo"), default=False, help_text=_("Shown on the variety card.")
    )

    thumb = _webp_spec(400)
    medium = _webp_spec(1000)
    large = _webp_spec(1800)

    class Meta:
        verbose_name = _("photo")
        verbose_name_plural = _("photos")
        ordering = ["order", "pk"]

    def __str__(self) -> str:
        return self.alt or PurePosixPath(self.image.name).name

    def save(self, *args: Any, **kwargs: Any) -> None:
        # Only one main photo per variety: marking a new one unmarks the previous one.
        # (Not a DB constraint: model validation would reject swapping the main photo in
        # the admin, because it runs before the previous main photo is saved.)
        with transaction.atomic():
            if self.is_main:
                VarietyPhoto.objects.filter(variety_id=self.variety_id, is_main=True).exclude(
                    pk=self.pk
                ).update(is_main=False)
            super().save(*args, **kwargs)


class VarietyVideo(models.Model):
    """A YouTube video about a variety."""

    variety = models.ForeignKey(
        Variety, verbose_name=_("variety"), on_delete=models.CASCADE, related_name="videos"
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
        validate_youtube_url(self.youtube_url)
        self.youtube_id = parse_youtube_id(self.youtube_url) or ""
        super().save(*args, **kwargs)
