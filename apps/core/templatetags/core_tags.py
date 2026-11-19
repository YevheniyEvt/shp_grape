"""Template tags shared by the project templates."""

from django import template

from apps.core.version import get_project_version

register = template.Library()


@register.simple_tag
def project_version() -> str:
    """The project version from pyproject.toml, e.g. `0.2.0`."""
    return get_project_version()
