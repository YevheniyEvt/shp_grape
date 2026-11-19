"""Public read-only API of the content app (`/api/content/`)."""

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.content.models import SiteSettings
from apps.content.serializers import SiteSettingsSerializer


class SiteSettingsView(APIView):
    """Public site settings (page background)."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    @extend_schema(responses=SiteSettingsSerializer)
    def get(self, request: Request) -> Response:
        settings = SiteSettings.get_solo()
        return Response(SiteSettingsSerializer(settings, context={"request": request}).data)
