"""Serializers of the content API (translated fields follow Accept-Language)."""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.catalog.models import VarietyPhoto
from apps.catalog.serializers import VarietyListSerializer, absolute_url
from apps.content.models import (
    Article,
    ArticlePhoto,
    ArticleVideo,
    GalleryAlbum,
    GalleryPhoto,
    News,
    Page,
    SiteSettings,
    UsefulLink,
)
from apps.content.selectors import FeedPhoto


def _file_url(serializer: serializers.Serializer, field) -> str | None:
    return absolute_url(serializer, field.url) if field else None


class MapPointSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class SocialLinksSerializer(serializers.Serializer):
    facebook = serializers.URLField(allow_blank=True)
    instagram = serializers.URLField(allow_blank=True)
    youtube = serializers.URLField(allow_blank=True)
    telegram = serializers.URLField(allow_blank=True)
    forum = serializers.URLField(allow_blank=True)


class SiteSettingsSerializer(serializers.ModelSerializer):
    """Contacts, links and the page background used by the header and footer of every page."""

    phones = serializers.ListField(child=serializers.CharField(), source="phone_list")
    map = serializers.SerializerMethodField()
    price_list = serializers.SerializerMethodField()
    social = serializers.SerializerMethodField()
    background_image = serializers.SerializerMethodField(
        help_text="WebP rendition of the uploaded background, or null for the built-in one."
    )

    class Meta:
        model = SiteSettings
        fields = [
            "site_name",
            "tagline",
            "owner_name",
            "phones",
            "email",
            "address",
            "map",
            "price_list",
            "social",
            "show_background",
            "background_image",
        ]

    @extend_schema_field(MapPointSerializer(allow_null=True))
    def get_map(self, obj: SiteSettings) -> dict | None:
        if obj.map_latitude is None or obj.map_longitude is None:
            return None
        return {"latitude": float(obj.map_latitude), "longitude": float(obj.map_longitude)}

    def get_price_list(self, obj: SiteSettings) -> str | None:
        return _file_url(self, obj.price_list)

    @extend_schema_field(SocialLinksSerializer)
    def get_social(self, obj: SiteSettings) -> dict[str, str]:
        return {
            "facebook": obj.facebook_url,
            "instagram": obj.instagram_url,
            "youtube": obj.youtube_url,
            "telegram": obj.telegram_url,
            "forum": obj.forum_url,
        }

    def get_background_image(self, obj: SiteSettings) -> str | None:
        return absolute_url(self, obj.background.url) if obj.background_image else None


class CoverSerializer(serializers.Serializer):
    card = serializers.URLField()
    large = serializers.URLField()
    width = serializers.IntegerField(allow_null=True)
    height = serializers.IntegerField(allow_null=True)


class PublicationListSerializer(serializers.ModelSerializer):
    cover = serializers.SerializerMethodField()

    class Meta:
        model = News
        fields = ["id", "slug", "title", "published_at", "cover"]

    @extend_schema_field(CoverSerializer(allow_null=True))
    def get_cover(self, obj: News | Article) -> dict | None:
        if not obj.cover:
            return None
        return {
            "card": absolute_url(self, obj.cover_card.url),
            "large": absolute_url(self, obj.cover_large.url),
            "width": obj.cover.width,
            "height": obj.cover.height,
        }


class NewsListSerializer(PublicationListSerializer):
    pass


class NewsDetailSerializer(PublicationListSerializer):
    class Meta(PublicationListSerializer.Meta):
        fields = [*PublicationListSerializer.Meta.fields, "body"]


class ArticleListSerializer(PublicationListSerializer):
    class Meta(PublicationListSerializer.Meta):
        model = Article
        fields = [*PublicationListSerializer.Meta.fields, "excerpt", "author"]


class ContentPhotoSerializer(serializers.Serializer):
    """A photo with WebP renditions: `thumb` (400 px), `medium` (1000 px), `large` (1800 px)."""

    id = serializers.IntegerField()
    caption = serializers.CharField()
    alt = serializers.SerializerMethodField()
    width = serializers.IntegerField(allow_null=True)
    height = serializers.IntegerField(allow_null=True)
    thumb = serializers.SerializerMethodField()
    medium = serializers.SerializerMethodField()
    large = serializers.SerializerMethodField()

    def get_alt(self, photo: ArticlePhoto | GalleryPhoto) -> str:
        return photo.caption or self.context.get("alt_fallback", "")

    def get_thumb(self, photo) -> str:
        return absolute_url(self, photo.thumb.url)

    def get_medium(self, photo) -> str:
        return absolute_url(self, photo.medium.url)

    def get_large(self, photo) -> str:
        return absolute_url(self, photo.large.url)


class ArticleVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleVideo
        fields = ["id", "youtube_id", "youtube_url", "title"]


class ArticleDetailSerializer(ArticleListSerializer):
    photos = serializers.SerializerMethodField()
    videos = ArticleVideoSerializer(many=True)

    class Meta(ArticleListSerializer.Meta):
        fields = [*ArticleListSerializer.Meta.fields, "body", "photos", "videos"]

    @extend_schema_field(ContentPhotoSerializer(many=True))
    def get_photos(self, article: Article) -> list[dict]:
        context = self.context | {"alt_fallback": article.title}
        return ContentPhotoSerializer(article.photos.all(), many=True, context=context).data


class UsefulLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsefulLink
        fields = ["id", "title", "url", "description"]


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ["slug", "title", "body", "updated_at"]


class AlbumListSerializer(serializers.ModelSerializer):
    cover = serializers.SerializerMethodField()
    photo_count = serializers.SerializerMethodField()

    class Meta:
        model = GalleryAlbum
        fields = ["id", "slug", "title", "description", "date", "photo_count", "cover"]

    def _photos(self, album: GalleryAlbum) -> list[GalleryPhoto]:
        return getattr(album, "ordered_photos", None) or list(album.photos.all())

    def get_photo_count(self, album: GalleryAlbum) -> int:
        count = getattr(album, "photo_count", None)
        return count if count is not None else len(self._photos(album))

    @extend_schema_field(ContentPhotoSerializer(allow_null=True))
    def get_cover(self, album: GalleryAlbum) -> dict | None:
        photos = self._photos(album)
        if not photos:
            return None
        context = self.context | {"alt_fallback": album.title}
        return ContentPhotoSerializer(photos[0], context=context).data


class AlbumDetailSerializer(AlbumListSerializer):
    photos = serializers.SerializerMethodField()

    class Meta(AlbumListSerializer.Meta):
        fields = [*AlbumListSerializer.Meta.fields, "photos"]

    @extend_schema_field(ContentPhotoSerializer(many=True))
    def get_photos(self, album: GalleryAlbum) -> list[dict]:
        context = self.context | {"alt_fallback": album.title}
        return ContentPhotoSerializer(self._photos(album), many=True, context=context).data


class FeedSourceSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=["album", "variety"])
    slug = serializers.CharField()
    title = serializers.CharField()


class FeedPhotoSerializer(serializers.Serializer):
    """A photo of the "All photos" feed with a link to its album or variety."""

    id = serializers.SerializerMethodField()
    alt = serializers.SerializerMethodField()
    width = serializers.SerializerMethodField()
    height = serializers.SerializerMethodField()
    thumb = serializers.SerializerMethodField()
    medium = serializers.SerializerMethodField()
    large = serializers.SerializerMethodField()
    source = serializers.SerializerMethodField()

    def get_id(self, item: FeedPhoto) -> str:
        return f"{item.kind}-{item.photo.pk}"

    def get_alt(self, item: FeedPhoto) -> str:
        photo = item.photo
        if isinstance(photo, VarietyPhoto):
            return photo.alt or photo.variety.name
        return photo.caption or photo.album.title

    def get_width(self, item: FeedPhoto) -> int | None:
        return item.photo.width

    def get_height(self, item: FeedPhoto) -> int | None:
        return item.photo.height

    def get_thumb(self, item: FeedPhoto) -> str:
        return absolute_url(self, item.photo.thumb.url)

    def get_medium(self, item: FeedPhoto) -> str:
        return absolute_url(self, item.photo.medium.url)

    def get_large(self, item: FeedPhoto) -> str:
        return absolute_url(self, item.photo.large.url)

    @extend_schema_field(FeedSourceSerializer)
    def get_source(self, item: FeedPhoto) -> dict[str, str]:
        photo = item.photo
        if isinstance(photo, VarietyPhoto):
            return {"kind": "variety", "slug": photo.variety.slug, "title": photo.variety.name}
        return {"kind": "album", "slug": photo.album.slug, "title": photo.album.title}


class HomeSerializer(serializers.Serializer):
    """Everything the home page needs in one request."""

    welcome = serializers.CharField()
    hero_image = serializers.URLField(allow_null=True)
    latest_news = NewsListSerializer(allow_null=True)
    featured_varieties = VarietyListSerializer(many=True)
    latest_articles = ArticleListSerializer(many=True)
