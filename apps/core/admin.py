"""Admin helpers shared by all apps."""

from typing import Any

from django.http import HttpRequest


def _without(fields: Any, name: str) -> list:
    """Drop `name` from a fieldset's `fields`, including from grouped (tuple) rows."""
    result = []
    for field in fields:
        if isinstance(field, list | tuple):
            row = [item for item in field if item != name]
            if row:
                result.append(tuple(row))
        elif field != name:
            result.append(field)
    return result


class AutoSlugAdminMixin:
    """
    Admin for `AutoSlugMixin` models: the slug is generated, never typed in.

    The add form has no slug field; the change form shows it read-only.
    """

    def get_readonly_fields(self, request: HttpRequest, obj: Any = None) -> list[str]:
        readonly = list(super().get_readonly_fields(request, obj))  # type: ignore[misc]
        return readonly if "slug" in readonly else [*readonly, "slug"]

    def get_fieldsets(self, request: HttpRequest, obj: Any = None) -> list:
        fieldsets = super().get_fieldsets(request, obj)  # type: ignore[misc]
        if obj is not None:
            return fieldsets
        return [
            (title, {**options, "fields": _without(options["fields"], "slug")})
            for title, options in fieldsets
        ]
