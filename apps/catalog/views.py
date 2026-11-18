"""Public read-only API of the catalog (`/api/catalog/`)."""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import generics, serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog import selectors, services
from apps.catalog.filters import VarietyFilter
from apps.catalog.serializers import (
    FilterOptionsSerializer,
    RandomPhotoSerializer,
    VarietyDetailSerializer,
    VarietyListSerializer,
)

RANDOM_PHOTOS_DEFAULT = 10
RANDOM_PHOTOS_MAX = 30


class PublicAPIMixin:
    """Anonymous read access without session authentication (and therefore without CSRF)."""

    permission_classes = [AllowAny]
    authentication_classes: list = []


class VarietyPagination(PageNumberPagination):
    page_size = 24
    page_size_query_param = "page_size"
    max_page_size = 100


class VarietyListView(PublicAPIMixin, generics.ListAPIView):
    """Published varieties for the catalog, with filters, search and ordering."""

    serializer_class = VarietyListSerializer
    pagination_class = VarietyPagination
    filterset_class = VarietyFilter

    def get_queryset(self):
        return selectors.variety_list()


class VarietyDetailView(PublicAPIMixin, generics.RetrieveAPIView):
    """A published variety with all photos, videos and similar varieties."""

    serializer_class = VarietyDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return selectors.variety_detail_queryset()

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        variety = self.get_object()
        context = self.get_serializer_context() | {"similar": selectors.similar_varieties(variety)}
        return Response(self.get_serializer_class()(variety, context=context).data)


def visitor_id(request: Request) -> str:
    """Identify a visitor for view counting by IP address and browser."""
    address = request.META.get("REMOTE_ADDR", "")
    agent = request.META.get("HTTP_USER_AGENT", "")
    return f"{address}|{agent}"


class VarietyViewCountView(PublicAPIMixin, APIView):
    """Register a page view of a variety (counted once per visitor within a few hours)."""

    @extend_schema(
        request=None,
        responses=inline_serializer(
            name="VarietyViewCounted", fields={"counted": serializers.BooleanField()}
        ),
    )
    def post(self, request: Request, slug: str) -> Response:
        variety = get_object_or_404(selectors.published_varieties(), slug=slug)
        counted = services.register_view(variety, visitor_id(request))
        return Response({"counted": counted})


class FilterOptionsView(PublicAPIMixin, APIView):
    """Reference-list values and characteristic bounds for the advanced search form."""

    @extend_schema(responses=FilterOptionsSerializer)
    def get(self, request: Request) -> Response:
        return Response(FilterOptionsSerializer(selectors.filter_options()).data)


class LettersView(PublicAPIMixin, APIView):
    """Letters of the current language that start at least one published variety name."""

    @extend_schema(responses=serializers.ListSerializer(child=serializers.CharField()))
    def get(self, request: Request) -> Response:
        return Response(selectors.available_letters())


class RandomPhotosView(PublicAPIMixin, APIView):
    """Random variety photos for the footer, each linking to its variety."""

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "limit",
                int,
                description=f"1–{RANDOM_PHOTOS_MAX}, default {RANDOM_PHOTOS_DEFAULT}",
            )
        ],
        responses=RandomPhotoSerializer(many=True),
    )
    def get(self, request: Request) -> Response:
        try:
            limit = int(request.query_params.get("limit", RANDOM_PHOTOS_DEFAULT))
        except ValueError:
            limit = RANDOM_PHOTOS_DEFAULT
        limit = max(1, min(limit, RANDOM_PHOTOS_MAX))
        photos = selectors.random_photos(limit)
        return Response(RandomPhotoSerializer(photos, many=True, context={"request": request}).data)
