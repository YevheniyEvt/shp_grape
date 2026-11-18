"""Shared abstract models."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    """Abstract base model with creation and modification timestamps."""

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        abstract = True


class SlugNaturalKeyManager(models.Manager):
    """Manager resolving objects by their slug, the natural key used by fixtures and imports."""

    def get_by_natural_key(self, slug: str):
        return self.get(slug=slug)
