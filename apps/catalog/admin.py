"""Admin of the catalog: varieties with sortable photo and video inlines, reference lists."""

from adminsortable2.admin import SortableAdminBase, SortableAdminMixin, SortableTabularInline
from django import forms
from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TabbedTranslationAdmin, TranslationTabularInline

from apps.catalog import services
from apps.catalog.models import Variety, VarietyPhoto, VarietyVideo
from apps.catalog.selectors import DICTIONARY_MODELS, card_photos_prefetch
from apps.core.admin import AutoSlugAdminMixin


def photo_preview(photo: VarietyPhoto | None, size: int = 80) -> str:
    if photo is None or not photo.image:
        return "—"
    return format_html(
        '<img src="{}" alt="" style="max-width:{}px;max-height:{}px;border-radius:4px">',
        photo.thumb.url,
        size,
        size,
    )


class DictionaryAdmin(AutoSlugAdminMixin, SortableAdminMixin, TabbedTranslationAdmin):
    list_display = ["name", "slug", "variety_count"]
    search_fields = ["name_uk", "name_en", "slug"]

    @admin.display(description=_("varieties"))
    def variety_count(self, obj) -> int:
        return obj.varieties.count()


for model in DICTIONARY_MODELS.values():
    admin.site.register(model, DictionaryAdmin)


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    """Accepts several images at once and validates each of them."""

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("widget", MultipleFileInput(attrs={"accept": "image/*"}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_clean = super().clean
        if isinstance(data, list | tuple):
            return [single_clean(item, initial) for item in data]
        return [single_clean(data, initial)] if data else []


class VarietyAdminForm(forms.ModelForm):
    upload_photos = MultipleImageField(
        label=_("Add photos"),
        required=False,
        help_text=_("Select several files at once; they are added after the existing photos."),
    )

    class Meta:
        model = Variety
        exclude: list[str] = []


class VarietyPhotoInline(SortableTabularInline, TranslationTabularInline):
    model = VarietyPhoto
    fields = ["preview", "image", "alt", "is_main"]
    readonly_fields = ["preview"]
    extra = 0

    @admin.display(description=_("preview"))
    def preview(self, photo: VarietyPhoto) -> str:
        return photo_preview(photo if photo.pk else None)


class VarietyVideoInline(SortableTabularInline, TranslationTabularInline):
    model = VarietyVideo
    fields = ["youtube_url", "title"]
    extra = 0


@admin.register(Variety)
class VarietyAdmin(AutoSlugAdminMixin, SortableAdminBase, TabbedTranslationAdmin):
    form = VarietyAdminForm

    class Media:
        css = {"all": ["core/admin.css"]}

    inlines = [VarietyPhotoInline, VarietyVideoInline]
    list_display = [
        "thumbnail",
        "name",
        "ripening",
        "cutting_price",
        "cutting_available",
        "sapling_price",
        "sapling_available",
        "is_featured",
        "is_published",
        "views_count",
    ]
    list_display_links = ["thumbnail", "name"]
    list_editable = [
        "cutting_price",
        "cutting_available",
        "sapling_price",
        "sapling_available",
        "is_featured",
        "is_published",
    ]
    list_filter = [
        "is_published",
        "is_featured",
        "cutting_available",
        "sapling_available",
        "ripening",
        "berry_color",
        "taste",
    ]
    list_select_related = ["ripening"]
    search_fields = ["name_uk", "name_en", "alt_names_uk", "alt_names_en", "slug"]
    readonly_fields = ["views_count", "created_at", "updated_at"]
    fieldsets = [
        (None, {"fields": ["name", "slug", "alt_names", "author", "is_published", "is_featured"]}),
        (
            _("Characteristics"),
            {
                "fields": [
                    "ripening",
                    "berry_color",
                    "pulp",
                    "taste",
                    "vigor",
                    ("bunch_weight_min", "bunch_weight_max"),
                    ("berry_weight_min", "berry_weight_max"),
                    ("berry_size_min", "berry_size_max"),
                    ("disease_susceptibility_min", "disease_susceptibility_max"),
                    "frost_resistance",
                ]
            },
        ),
        (
            _("Prices and availability"),
            {
                "fields": [
                    ("cutting_price", "cutting_available"),
                    ("sapling_price", "sapling_available"),
                ]
            },
        ),
        (_("Description"), {"fields": ["description"]}),
        (_("Photos"), {"fields": ["upload_photos"]}),
        (_("Statistics"), {"fields": ["views_count", "created_at", "updated_at"]}),
    ]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Variety]:
        return super().get_queryset(request).prefetch_related(card_photos_prefetch())

    @admin.display(description=_("photo"))
    def thumbnail(self, variety: Variety) -> str:
        photos = getattr(variety, "card_photos", None) or []
        return photo_preview(photos[0] if photos else None, size=60)

    def save_related(self, request: HttpRequest, form, formsets, change) -> None:
        super().save_related(request, form, formsets, change)
        files = form.cleaned_data.get("upload_photos") or []
        if files:
            services.add_photos(form.instance, files)
