"""Serializers of the content API."""

from rest_framework import serializers

from apps.content.models import SiteSettings


class SiteSettingsSerializer(serializers.ModelSerializer):
    background_image = serializers.SerializerMethodField(
        help_text="WebP rendition of the uploaded background, or null for the built-in one."
    )

    class Meta:
        model = SiteSettings
        fields = ["show_background", "background_image"]

    def get_background_image(self, obj: SiteSettings) -> str | None:
        if not obj.background_image:
            return None
        request = self.context.get("request")
        url = obj.background.url
        return request.build_absolute_uri(url) if request else url
