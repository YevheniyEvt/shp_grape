"""
Automatic slugs from Ukrainian names.

Transliteration follows the official Ukrainian table (Cabinet of Ministers resolution
No. 55, 2010): letters `є`, `ї`, `й`, `ю`, `я` get a separate spelling at the beginning
of a word, `зг` becomes `zgh` to keep it distinct from `ж`, and the soft sign and
apostrophes are dropped.

Slugs are generated once, when an object is first saved with an empty slug, and never
change on rename, so that public URLs stay stable.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from collections.abc import Callable

# Letters spelled the same in any position of a word.
_BASE: dict[str, str] = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "h",
    "ґ": "g",
    "д": "d",
    "е": "e",
    "є": "ie",
    "ж": "zh",
    "з": "z",
    "и": "y",
    "і": "i",
    "ї": "i",
    "й": "i",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "kh",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "shch",
    "ь": "",
    "ю": "iu",
    "я": "ia",
    # Russian letters occasionally present in alternative spellings.
    "ё": "io",
    "ъ": "",
    "ы": "y",
    "э": "e",
}

# Spelling at the beginning of a word.
_INITIAL: dict[str, str] = {
    "є": "ye",
    "ї": "yi",
    "й": "y",
    "ю": "yu",
    "я": "ya",
    "ё": "yo",
}

# Apostrophe variants used in Ukrainian texts; they belong to the word and are dropped.
_APOSTROPHES = frozenset("'’ʼ`‘")


def transliterate(text: str) -> str:
    """Transliterate Ukrainian text into Latin letters (KMU 2010), keeping other characters."""
    result: list[str] = []
    at_word_start = True
    previous = ""
    for char in text:
        lower = char.lower()
        if lower in _APOSTROPHES:
            continue
        if lower in _BASE:
            if at_word_start and lower in _INITIAL:
                latin = _INITIAL[lower]
            elif lower == "г" and previous == "з":
                latin = "gh"
            else:
                latin = _BASE[lower]
            if char != lower and latin:
                latin = latin[0].upper() + latin[1:]
            result.append(latin)
            at_word_start = False
        else:
            result.append(char)
            at_word_start = not char.isalnum()
        previous = lower
    return "".join(result)


def slugify_uk(text: str) -> str:
    """Build an ASCII slug from Ukrainian text: `Ранній Зоряний` -> `rannii-zorianyi`."""
    return slugify(transliterate(text))


def unique_slug(base: str, exists: Callable[[str], bool], max_length: int = 50) -> str:
    """
    Return `base` or `base-2`, `base-3`, ... – the first candidate for which `exists` is False.

    The base is trimmed so that the suffix always fits into `max_length`.
    """
    base = base[:max_length].strip("-")
    candidate = base
    number = 1
    while exists(candidate):
        number += 1
        suffix = f"-{number}"
        candidate = f"{base[: max_length - len(suffix)].rstrip('-')}{suffix}"
    return candidate


class AutoSlugMixin(models.Model):
    """
    Model mixin with a unique slug generated from the Ukrainian value of `slug_source_field`.

    With django-modeltranslation the source field has per-language columns; the default-language
    column (`name_uk`) is preferred so that the slug does not depend on the active language.
    """

    slug_source_field = "name"
    slug_fallback = "item"

    slug = models.SlugField(
        _("slug"),
        max_length=120,
        unique=True,
        blank=True,
        help_text=_(
            "Part of the page address. Generated from the Ukrainian name and kept "
            "when the object is renamed."
        ),
    )

    class Meta:
        abstract = True

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.slug:
            self.slug = self.generate_slug()
        super().save(*args, **kwargs)

    def get_slug_source(self) -> str:
        """Return the text the slug is built from."""
        field = self.slug_source_field
        localized: Any = getattr(self, f"{field}_{settings.LANGUAGE_CODE}", None)
        return str(localized or getattr(self, field, "") or "")

    def generate_slug(self) -> str:
        """Build a slug that is unique among objects of this model."""
        max_length = self._meta.get_field("slug").max_length or 50
        base = slugify_uk(self.get_slug_source()) or self.slug_fallback
        others = type(self)._default_manager.all()
        if self.pk:
            others = others.exclude(pk=self.pk)
        return unique_slug(base, lambda value: others.filter(slug=value).exists(), max_length)
