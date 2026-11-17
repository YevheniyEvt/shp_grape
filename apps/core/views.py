"""API views of the core app."""

from django.http import Http404
from django.utils import translation
from django.views.i18n import JSONCatalog
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core import services


class HealthView(APIView):
    """Report service status, database connectivity and the deployed version."""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        responses=inline_serializer(
            name="Health",
            fields={
                "status": serializers.CharField(),
                "database": serializers.CharField(),
                "version": serializers.CharField(),
            },
        )
    )
    def get(self, request: Request) -> Response:
        health = services.check_health()
        return Response(
            {"status": health.status, "database": health.database, "version": health.version},
            status=status.HTTP_200_OK if health.is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class LanguagesView(APIView):
    """List the site languages for the language switcher."""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        responses=inline_serializer(
            name="Language",
            many=True,
            fields={
                "code": serializers.CharField(),
                "name": serializers.CharField(),
                "is_default": serializers.BooleanField(),
            },
        )
    )
    def get(self, request: Request) -> Response:
        return Response(services.get_languages())


class TranslationCatalogView(JSONCatalog):
    """
    Return the compiled `djangojs` catalog (frontend UI strings) for a language.

    Translations come from `locale/<lang>/LC_MESSAGES/djangojs.po` (compiled to `.mo`).
    Only project packages are included, so Django admin JS strings are not shipped.
    """

    domain = "djangojs"
    packages = ["apps.core"]

    def get(self, request, *args, **kwargs):
        lang = kwargs.pop("lang")
        if not services.is_supported_language(lang):
            raise Http404("Unsupported language")
        with translation.override(lang):
            return super().get(request, *args, **kwargs)
