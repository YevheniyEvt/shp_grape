"""Admin of the content app."""

from adminsortable2.admin import SortableAdminBase, SortableAdminMixin, SortableTabularInline
from django import forms
from django.contrib import admin
from django.http import HttpRequest
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TabbedTranslationAdmin, TranslationTabularInline
from solo.admin import SingletonModelAdmin

from apps.catalog.admin import MultipleImageField
from apps.content import services
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
from apps.core.admin import AutoSlugAdminMixin

ADMIN_CSS = {"all": ["core/admin.css"]}


def image_preview(url: str | None, size: int = 80) -> str:
    if not url:
        return "—"
    return format_html(
        '<img src="{}" alt="" style="max-width:{}px;max-height:{}px;border-radius:4px">',
        url,
        size,
        size,
    )


def upload_field() -> MultipleImageField:
    return MultipleImageField(
        label=_("Add photos"),
        required=False,
        help_text=_("Select several files at once; they are added after the existing photos."),
    )


@admin.register(SiteSettings)
class SiteSettingsAdmin(SingletonModelAdmin, TabbedTranslationAdmin):
    fieldsets = [
        (_("Site"), {"fields": ["site_name", "tagline", "welcome", "hero_image", "hero_preview"]}),
        (
            _("Contacts"),
            {
                "fields": [
                    "owner_name",
                    "phones",
                    "email",
                    "address",
                    ("map_latitude", "map_longitude"),
                    "price_list",
                ]
            },
        ),
        (
            _("Links"),
            {
                "fields": [
                    "facebook_url",
                    "instagram_url",
                    "youtube_url",
                    "telegram_url",
                    "forum_url",
                ]
            },
        ),
        (
            _("Background"),
            {"fields": ["show_background", "background_image", "background_preview"]},
        ),
    ]
    readonly_fields = ["hero_preview", "background_preview"]

    class Media:
        css = ADMIN_CSS

    @admin.display(description=_("preview"))
    def hero_preview(self, obj: SiteSettings) -> str:
        return image_preview(obj.hero.url if obj.hero_image else None, 320)

    @admin.display(description=_("preview"))
    def background_preview(self, obj: SiteSettings) -> str:
        return image_preview(obj.background.url if obj.background_image else None, 480)


class PublicationAdmin(AutoSlugAdminMixin, TabbedTranslationAdmin):
    list_display = ["cover_thumbnail", "title", "published_at", "is_published"]
    list_display_links = ["cover_thumbnail", "title"]
    list_editable = ["is_published"]
    list_filter = ["is_published", "published_at"]
    search_fields = ["title_uk", "title_en", "slug"]
    date_hierarchy = "published_at"
    readonly_fields = ["created_at", "updated_at"]

    class Media:
        css = ADMIN_CSS

    @admin.display(description=_("cover"))
    def cover_thumbnail(self, obj: News | Article) -> str:
        return image_preview(obj.cover_card.url if obj.cover else None, 60)


@admin.register(News)
class NewsAdmin(PublicationAdmin):
    fieldsets = [
        (None, {"fields": ["title", "slug", "published_at", "is_published", "cover"]}),
        (_("Text"), {"fields": ["body"]}),
        (_("Statistics"), {"fields": ["created_at", "updated_at"]}),
    ]


class ArticleAdminForm(forms.ModelForm):
    upload_photos = upload_field()

    class Meta:
        model = Article
        exclude: list[str] = []


class ArticlePhotoInline(SortableTabularInline, TranslationTabularInline):
    model = ArticlePhoto
    fields = ["preview", "image", "caption"]
    readonly_fields = ["preview"]
    extra = 0

    @admin.display(description=_("preview"))
    def preview(self, photo: ArticlePhoto) -> str:
        return image_preview(photo.thumb.url if photo.pk and photo.image else None)


class ArticleVideoInline(SortableTabularInline, TranslationTabularInline):
    model = ArticleVideo
    fields = ["youtube_url", "title"]
    extra = 0


@admin.register(Article)
class ArticleAdmin(SortableAdminBase, PublicationAdmin):
    form = ArticleAdminForm
    inlines = [ArticlePhotoInline, ArticleVideoInline]
    list_display = ["cover_thumbnail", "title", "author", "published_at", "is_published"]
    fieldsets = [
        (None, {"fields": ["title", "slug", "author", "published_at", "is_published", "cover"]}),
        (_("Text"), {"fields": ["excerpt", "body"]}),
        (_("Photos"), {"fields": ["upload_photos"]}),
        (_("Statistics"), {"fields": ["created_at", "updated_at"]}),
    ]

    def save_related(self, request: HttpRequest, form, formsets, change) -> None:
        super().save_related(request, form, formsets, change)
        files = form.cleaned_data.get("upload_photos") or []
        if files:
            services.add_article_photos(form.instance, files)


@admin.register(UsefulLink)
class UsefulLinkAdmin(SortableAdminMixin, TabbedTranslationAdmin):
    list_display = ["title", "url"]
    search_fields = ["title_uk", "title_en", "url"]


@admin.register(Page)
class PageAdmin(AutoSlugAdminMixin, TabbedTranslationAdmin):
    list_display = ["title", "slug", "updated_at"]
    search_fields = ["title_uk", "title_en", "slug"]
    fields = ["title", "slug", "body"]

    class Media:
        css = ADMIN_CSS


class GalleryAlbumAdminForm(forms.ModelForm):
    upload_photos = upload_field()

    class Meta:
        model = GalleryAlbum
        exclude: list[str] = []


class GalleryPhotoInline(SortableTabularInline, TranslationTabularInline):
    model = GalleryPhoto
    fields = ["preview", "image", "caption"]
    readonly_fields = ["preview"]
    extra = 0

    @admin.display(description=_("preview"))
    def preview(self, photo: GalleryPhoto) -> str:
        return image_preview(photo.thumb.url if photo.pk and photo.image else None)


@admin.register(GalleryAlbum)
class GalleryAlbumAdmin(
    AutoSlugAdminMixin, SortableAdminMixin, SortableAdminBase, TabbedTranslationAdmin
):
    form = GalleryAlbumAdminForm
    inlines = [GalleryPhotoInline]
    list_display = ["title", "date", "photo_count", "is_published"]
    list_editable = ["is_published"]
    search_fields = ["title_uk", "title_en", "slug"]
    fieldsets = [
        (None, {"fields": ["title", "slug", "description", "date", "is_published"]}),
        (_("Photos"), {"fields": ["upload_photos"]}),
    ]

    @admin.display(description=_("photos"))
    def photo_count(self, album: GalleryAlbum) -> int:
        return album.photos.count()

    def save_related(self, request: HttpRequest, form, formsets, change) -> None:
        super().save_related(request, form, formsets, change)
        files = form.cleaned_data.get("upload_photos") or []
        if files:
            services.add_album_photos(form.instance, files)
