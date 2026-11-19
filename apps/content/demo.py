"""
Demo content for development and the demo site (`manage.py seed_demo`).

All texts, names and contacts are invented. Values are frozen here; objects are found by slug
(links by URL), so re-running the command never duplicates or overwrites anything.
"""

import datetime
from dataclasses import dataclass, field

from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from apps.catalog.demo import placeholder_photo
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

# Fill only empty settings fields: the real owner's data is never overwritten.
SETTINGS = {
    "tagline_uk": "Живці та саджанці столових сортів",
    "tagline_en": "Cuttings and saplings of table varieties",
    "welcome_uk": (
        "<p>Вітаємо на сайті нашого виноградника! Ми вирощуємо столові сорти винограду "
        "й ділимося живцями та саджанцями з усіма, хто хоче мати власну лозу.</p>"
    ),
    "welcome_en": (
        "<p>Welcome to our vineyard! We grow table grape varieties and share cuttings "
        "and saplings with everyone who wants a vine of their own.</p>"
    ),
    "owner_name_uk": "Олена Демченко",
    "owner_name_en": "Olena Demchenko",
    "phones": "+380 (00) 000-00-00\n+380 (00) 000-00-01",
    "email": "info@example.com",
    "address_uk": "с. Демонстраційне, Україна",
    "address_en": "Demo village, Ukraine",
    "map_latitude": "49.000000",
    "map_longitude": "31.400000",
}

ABOUT_BODY = {
    "body_uk": (
        "<p>Наш виноградник — сімейна справа. На кількох сотках ми зібрали колекцію столових "
        "сортів різних термінів дозрівання й щороку перевіряємо нові.</p>"
        "<h2>Що ми пропонуємо</h2><ul><li>живці з маточних кущів;</li>"
        "<li>однорічні саджанці;</li><li>поради щодо вибору сорту й догляду.</li></ul>"
    ),
    "body_en": (
        "<p>Our vineyard is a family business. On a small plot we have gathered a collection of "
        "table varieties of different ripening periods and test new ones every year.</p>"
        "<h2>What we offer</h2><ul><li>cuttings from mother vines;</li>"
        "<li>one-year-old saplings;</li><li>advice on choosing and growing varieties.</li></ul>"
    ),
}


@dataclass(frozen=True)
class DemoPublication:
    slug: str
    fields: dict
    days_ago: int
    photo_count: int = 0
    videos: tuple[tuple[str, str, str], ...] = ()


DEMO_NEWS = (
    DemoPublication(
        slug="startuvav-sezon-zhyvtsiv",
        fields={
            "title_uk": "Стартував сезон живців",
            "title_en": "Cutting season has started",
            "body_uk": "<p>Ми почали приймати замовлення на живці. Відправляємо щотижня.</p>",
            "body_en": "<p>We have started taking orders for cuttings. Parcels go out weekly.</p>",
        },
        days_ago=2,
        photo_count=1,
    ),
    DemoPublication(
        slug="novi-sorty-v-kolektsii",
        fields={
            "title_uk": "Нові сорти в колекції",
            "title_en": "New varieties in the collection",
            "body_uk": "<p>Цього року колекція поповнилася двома ранніми сортами.</p>",
            "body_en": "<p>This year two early varieties joined the collection.</p>",
        },
        days_ago=20,
    ),
)

DEMO_ARTICLES = (
    DemoPublication(
        slug="yak-posadyty-sadzhanets",
        fields={
            "title_uk": "Як посадити саджанець",
            "title_en": "How to plant a sapling",
            "author_uk": "Олена Демченко",
            "author_en": "Olena Demchenko",
            "excerpt_uk": "Покрокова інструкція: місце, яма, полив і перший рік догляду.",
            "excerpt_en": "Step by step: the spot, the pit, watering and the first year of care.",
            "body_uk": (
                "<p>Оберіть сонячне місце, захищене від північних вітрів.</p>"
                "<h2>Посадкова яма</h2><p>Глибина й ширина — близько 60 см. "
                "На дно покладіть дренаж і перегній.</p>"
                "<h2>Полив</h2><p>Після посадки полийте двома відрами води.</p>"
            ),
            "body_en": (
                "<p>Choose a sunny spot sheltered from northern winds.</p>"
                "<h2>The pit</h2><p>About 60 cm deep and wide, "
                "with drainage and humus at the bottom.</p>"
                "<h2>Watering</h2><p>Water with two buckets after planting.</p>"
            ),
        },
        days_ago=5,
        photo_count=3,
        videos=(("https://youtu.be/Demo-Video3", "Посадка саджанця", "Planting a sapling"),),
    ),
    DemoPublication(
        slug="obrizka-vynohradu-voseny",
        fields={
            "title_uk": "Обрізка винограду восени",
            "title_en": "Pruning grapes in autumn",
            "author_uk": "Олена Демченко",
            "excerpt_uk": "Коли і як обрізати лозу перед зимою.",
            "body_uk": "<p>Обрізку починають після листопаду, коли лоза визріла.</p>",
        },
        days_ago=30,
        photo_count=2,
    ),
)

DEMO_LINKS = (
    (
        "https://uk.wikipedia.org/wiki/Виноград_справжній",
        {"title_uk": "Виноград справжній — Вікіпедія", "title_en": "Grapevine — Wikipedia (uk)"},
    ),
    (
        "https://uk.wikipedia.org/wiki/Виноградарство",
        {"title_uk": "Виноградарство — Вікіпедія", "title_en": "Viticulture — Wikipedia (uk)"},
    ),
    (
        "https://uk.wikipedia.org/wiki/Ампелографія",
        {
            "title_uk": "Ампелографія — наука про сорти",
            "title_en": "Ampelography — the study of varieties",
            "description_uk": "Як описують і розрізняють сорти винограду.",
            "description_en": "How grape varieties are described and told apart.",
        },
    ),
)

DEMO_ALBUM_SLUG = "zbir-vrozhaiu"
DEMO_ALBUM = {
    "title_uk": "Збір врожаю",
    "title_en": "Harvest",
    "description_uk": "Фото з цьогорічного збору винограду.",
    "description_en": "Photos from this year's grape harvest.",
}
DEMO_ALBUM_PHOTOS = 6
PHOTO_COLOURS = ("fioletovyi", "zhovtyi", "chervonyi", "synii", "bilyi", "chornyi")


@dataclass
class ContentReport:
    created: list[str] = field(default_factory=list)


def _image(title: str, index: int) -> ContentFile:
    colour = PHOTO_COLOURS[index % len(PHOTO_COLOURS)]
    return ContentFile(placeholder_photo(title, colour, index))


def seed_settings(report: ContentReport) -> None:
    settings = SiteSettings.get_solo()
    changed = [name for name, value in SETTINGS.items() if not getattr(settings, name)]
    for name in changed:
        setattr(settings, name, SETTINGS[name])
    if not settings.hero_image:
        settings.hero_image.save("hero.jpg", _image("Vineyard", 1), save=False)
        changed.append("hero_image")
    if changed:
        settings.save()
        report.created.append("settings")

    about = Page.objects.filter(slug=Page.ABOUT_SLUG).first()
    if about and "Розкажіть тут" in (about.body_uk or ""):
        for name, value in ABOUT_BODY.items():
            setattr(about, name, value)
        about.save()
        report.created.append("about")


def _seed_publications(model, items, report: ContentReport) -> None:
    today = timezone.localdate()
    for item in items:
        if model.objects.filter(slug=item.slug).exists():
            continue
        with transaction.atomic():
            obj = model(
                slug=item.slug,
                published_at=today - datetime.timedelta(days=item.days_ago),
                **item.fields,
            )
            title = item.fields.get("title_en") or item.slug
            if item.photo_count:
                obj.cover.save(f"{item.slug}.jpg", _image(title, 0), save=False)
            obj.save()
            if model is Article:
                for index in range(1, item.photo_count + 1):
                    photo = ArticlePhoto(article=obj, order=index)
                    photo.image.save(f"{item.slug}-{index}.jpg", _image(title, index), save=False)
                    photo.save()
                for order, (url, title_uk, title_en) in enumerate(item.videos):
                    ArticleVideo.objects.create(
                        article=obj,
                        youtube_url=url,
                        title_uk=title_uk,
                        title_en=title_en,
                        order=order,
                    )
        report.created.append(item.slug)


def seed_content() -> ContentReport:
    """Create demo settings, news, articles, links, the About page text and an album."""
    report = ContentReport()
    seed_settings(report)
    _seed_publications(News, DEMO_NEWS, report)
    _seed_publications(Article, DEMO_ARTICLES, report)

    for order, (url, fields) in enumerate(DEMO_LINKS):
        _link, created = UsefulLink.objects.get_or_create(
            url=url, defaults={"order": order, **fields}
        )
        if created:
            report.created.append(url)

    if not GalleryAlbum.objects.filter(slug=DEMO_ALBUM_SLUG).exists():
        with transaction.atomic():
            album = GalleryAlbum.objects.create(slug=DEMO_ALBUM_SLUG, **DEMO_ALBUM)
            for index in range(1, DEMO_ALBUM_PHOTOS + 1):
                photo = GalleryPhoto(album=album, order=index)
                photo.image.save(f"harvest-{index}.jpg", _image("Harvest", index), save=False)
                photo.save()
        report.created.append(DEMO_ALBUM_SLUG)
    return report


def delete_demo_content() -> int:
    """Delete demo news, articles, links and the album (settings and pages stay)."""
    deleted = 0
    deleted += News.objects.filter(slug__in=[item.slug for item in DEMO_NEWS]).delete()[0]
    deleted += Article.objects.filter(slug__in=[item.slug for item in DEMO_ARTICLES]).delete()[0]
    deleted += UsefulLink.objects.filter(url__in=[url for url, _ in DEMO_LINKS]).delete()[0]
    deleted += GalleryAlbum.objects.filter(slug=DEMO_ALBUM_SLUG).delete()[0]
    return deleted
