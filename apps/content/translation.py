"""django-modeltranslation registration of the content models."""

from modeltranslation.translator import TranslationOptions, register

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


@register(SiteSettings)
class SiteSettingsTranslationOptions(TranslationOptions):
    fields = ("site_name", "tagline", "welcome", "owner_name", "address")


@register(News)
class NewsTranslationOptions(TranslationOptions):
    fields = ("title", "body")
    required_languages = {"uk": ("title",)}


@register(Article)
class ArticleTranslationOptions(TranslationOptions):
    fields = ("title", "excerpt", "author", "body")
    required_languages = {"uk": ("title",)}


@register([ArticlePhoto, GalleryPhoto])
class PhotoTranslationOptions(TranslationOptions):
    fields = ("caption",)


@register(ArticleVideo)
class ArticleVideoTranslationOptions(TranslationOptions):
    fields = ("title",)


@register(UsefulLink)
class UsefulLinkTranslationOptions(TranslationOptions):
    fields = ("title", "description")
    required_languages = {"uk": ("title",)}


@register(Page)
class PageTranslationOptions(TranslationOptions):
    fields = ("title", "body")
    required_languages = {"uk": ("title",)}


@register(GalleryAlbum)
class GalleryAlbumTranslationOptions(TranslationOptions):
    fields = ("title", "description")
    required_languages = {"uk": ("title",)}
