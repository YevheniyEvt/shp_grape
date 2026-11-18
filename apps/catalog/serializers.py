"""Serializers of the catalog API.

Translated fields follow the active (Accept-Language) language."""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.catalog.models import Variety, VarietyPhoto, VarietyVideo


def absolute_url(serializer: serializers.Serializer, url: str) -> str:
    request = serializer.context.get("request")
    return request.build_absolute_uri(url) if request else url


class DictionarySerializer(serializers.Serializer):
    slug = serializers.SlugField()
    name = serializers.CharField()


class PhotoSerializer(serializers.ModelSerializer):
    """A photo with WebP renditions: `thumb` (400 px), `medium` (1000 px), `large` (1800 px)."""

    alt = serializers.SerializerMethodField()
    thumb = serializers.SerializerMethodField()
    medium = serializers.SerializerMethodField()
    large = serializers.SerializerMethodField()

    class Meta:
        model = VarietyPhoto
        fields = ["id", "alt", "width", "height", "thumb", "medium", "large"]

    def get_alt(self, photo: VarietyPhoto) -> str:
        return photo.alt or photo.variety.name

    def get_thumb(self, photo: VarietyPhoto) -> str:
        return absolute_url(self, photo.thumb.url)

    def get_medium(self, photo: VarietyPhoto) -> str:
        return absolute_url(self, photo.medium.url)

    def get_large(self, photo: VarietyPhoto) -> str:
        return absolute_url(self, photo.large.url)


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = VarietyVideo
        fields = ["id", "youtube_id", "youtube_url", "title"]


class VarietyListSerializer(serializers.ModelSerializer):
    """Compact variety for catalog cards."""

    main_photo = serializers.SerializerMethodField()
    ripening = DictionarySerializer(allow_null=True)
    berry_color = DictionarySerializer(allow_null=True)

    class Meta:
        model = Variety
        fields = [
            "id",
            "slug",
            "name",
            "main_photo",
            "ripening",
            "berry_color",
            "bunch_weight_min",
            "bunch_weight_max",
            "berry_weight_min",
            "berry_weight_max",
            "frost_resistance",
            "cutting_price",
            "cutting_available",
            "sapling_price",
            "sapling_available",
            "is_featured",
        ]

    @extend_schema_field(PhotoSerializer(allow_null=True))
    def get_main_photo(self, variety: Variety) -> dict | None:
        photos = getattr(variety, "card_photos", None)
        if photos is None:
            photos = sorted(variety.photos.all(), key=lambda p: (not p.is_main, p.order, p.pk))
        return PhotoSerializer(photos[0], context=self.context).data if photos else None


class VarietyDetailSerializer(VarietyListSerializer):
    """Full variety for its page, with all photos, videos and similar varieties."""

    pulp = DictionarySerializer(allow_null=True)
    taste = DictionarySerializer(allow_null=True)
    vigor = DictionarySerializer(allow_null=True)
    photos = PhotoSerializer(many=True)
    videos = VideoSerializer(many=True)
    similar = serializers.SerializerMethodField()

    class Meta(VarietyListSerializer.Meta):
        fields = [
            *VarietyListSerializer.Meta.fields,
            "alt_names",
            "author",
            "pulp",
            "taste",
            "vigor",
            "berry_size_min",
            "berry_size_max",
            "disease_susceptibility_min",
            "disease_susceptibility_max",
            "description",
            "photos",
            "videos",
            "views_count",
            "similar",
        ]

    @extend_schema_field(VarietyListSerializer(many=True))
    def get_similar(self, variety: Variety) -> list[dict]:
        similar = self.context.get("similar", [])
        return VarietyListSerializer(similar, many=True, context=self.context).data


class NumberRangeSerializer(serializers.Serializer):
    min = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    max = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)


class RangesSerializer(serializers.Serializer):
    bunch_weight = NumberRangeSerializer()
    berry_weight = NumberRangeSerializer()
    berry_size = NumberRangeSerializer()
    disease = NumberRangeSerializer()
    frost = NumberRangeSerializer()


class FilterOptionsSerializer(serializers.Serializer):
    ripening = DictionarySerializer(many=True)
    berry_color = DictionarySerializer(many=True)
    pulp = DictionarySerializer(many=True)
    taste = DictionarySerializer(many=True)
    vigor = DictionarySerializer(many=True)
    ranges = RangesSerializer()


class VarietyRefSerializer(serializers.Serializer):
    slug = serializers.SlugField()
    name = serializers.CharField()


class RandomPhotoSerializer(PhotoSerializer):
    """A thumbnail linking to its variety (footer gallery)."""

    variety = VarietyRefSerializer()
    medium = None
    large = None

    class Meta(PhotoSerializer.Meta):
        fields = ["id", "alt", "width", "height", "thumb", "variety"]
