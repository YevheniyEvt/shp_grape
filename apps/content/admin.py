"""Admin of the content app."""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from solo.admin import SingletonModelAdmin

from apps.content.models import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(SingletonModelAdmin):
    fieldsets = [
        (
            _("Background"),
            {"fields": ["show_background", "background_image", "background_preview"]},
        ),
    ]
    readonly_fields = ["background_preview"]

    @admin.display(description=_("preview"))
    def background_preview(self, obj: SiteSettings) -> str:
        if not obj.background_image:
            return "—"
        return format_html(
            '<img src="{}" alt="" style="max-width:480px;max-height:270px;border-radius:4px">',
            obj.background.url,
        )
