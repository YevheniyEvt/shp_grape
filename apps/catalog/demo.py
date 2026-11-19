"""
Demo varieties for development and the demo site (`manage.py seed_demo`).

All names, breeders and texts are invented. The data is frozen here on purpose: the command
must create the same set on every database, independently of the factories used by tests
(factory-boy is a development-only dependency).
"""

import io
import random
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from PIL import Image, ImageDraw, ImageFont

from apps.catalog.models import (
    BerryColor,
    GrowthVigor,
    PulpConsistency,
    RipeningPeriod,
    Taste,
    Variety,
    VarietyPhoto,
    VarietyVideo,
)

PHOTOS_DIR = settings.BASE_DIR / "fixtures" / "demo" / "photos"
PHOTO_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp"})
PLACEHOLDER_SIZE = (1200, 900)

# Berry colour slug -> (berry fill, berry shadow) of the placeholder photos.
BERRY_PALETTE: dict[str, tuple[str, str]] = {
    "bilyi": ("#d9e3a5", "#a9b86a"),
    "zhovtyi": ("#f0cf6a", "#c39a2e"),
    "rozhevyi": ("#e7a0b4", "#b8657d"),
    "chervonyi": ("#c2414f", "#7f1f2b"),
    "fioletovyi": ("#8a52b8", "#4f2775"),
    "synii": ("#4b5fa8", "#26346b"),
    "chornyi": ("#3a2f4a", "#1b1424"),
}
DEFAULT_BERRY = ("#8a52b8", "#4f2775")

DICTIONARIES = {
    "ripening": RipeningPeriod,
    "berry_color": BerryColor,
    "pulp": PulpConsistency,
    "taste": Taste,
    "vigor": GrowthVigor,
}


@dataclass(frozen=True)
class DemoVideo:
    youtube_url: str
    title_uk: str
    title_en: str


@dataclass(frozen=True)
class DemoVariety:
    slug: str
    # Translated and plain model fields, passed to `Variety(...)` as is.
    fields: dict[str, Any]
    # Reference-list field -> slug of the value (see `catalog/0003_default_dictionaries`).
    dictionaries: dict[str, str]
    photo_count: int = 0
    videos: tuple[DemoVideo, ...] = field(default_factory=tuple)


def _d(value: str) -> Decimal:
    return Decimal(value)


DEMO_VARIETIES: tuple[DemoVariety, ...] = (
    DemoVariety(
        slug="rankovyi-ametyst",
        fields={
            "name_uk": "Ранковий Аметист",
            "name_en": "Morning Amethyst",
            "alt_names_uk": "Ранній Аметист, Аметист ранковий",
            "author_uk": "О. Демченко",
            "author_en": "O. Demchenko",
            "description_uk": (
                "<p>Дуже ранній столовий сорт з великими овальними ягодами фіолетового кольору. "
                "Грона конічні, помірно щільні, добре зберігаються на кущі.</p>"
                "<p>М'якоть м'ясисто-соковита, смак гармонійний з легкою свіжістю. "
                "Підходить для аматорських виноградників і невеликих ділянок.</p>"
            ),
            "description_en": (
                "<p>A very early table variety with large oval purple berries. "
                "The bunches are conical, moderately dense and hold well on the vine.</p>"
                "<p>The flesh is meaty and juicy with a harmonious, fresh taste. "
                "A good choice for hobby vineyards and small gardens.</p>"
            ),
            "bunch_weight_min": _d("0.5"),
            "bunch_weight_max": _d("0.8"),
            "berry_weight_min": _d("8"),
            "berry_weight_max": _d("10"),
            "berry_size_min": _d("24"),
            "berry_size_max": _d("28"),
            "disease_susceptibility_min": _d("2.5"),
            "disease_susceptibility_max": _d("3"),
            "frost_resistance": -23,
            "cutting_price": _d("30"),
            "cutting_available": True,
            "sapling_price": _d("120"),
            "sapling_available": True,
            "is_featured": True,
        },
        dictionaries={
            "ripening": "duzhe-rannii",
            "berry_color": "fioletovyi",
            "pulp": "miasysto-sokovyta",
            "taste": "harmoniinyi",
            "vigor": "sylnorosla",
        },
        photo_count=5,
        videos=(
            # Placeholder ids in a valid format; replace them with real videos in the admin.
            DemoVideo(
                "https://www.youtube.com/watch?v=Demo-Video1",
                "Огляд сорту на кущі",
                "The variety on the vine",
            ),
            DemoVideo(
                "https://youtu.be/Demo-Video2",
                "Дегустація врожаю",
                "Tasting the harvest",
            ),
        ),
    ),
    DemoVariety(
        slug="burshtynova-zoria",
        fields={
            "name_uk": "Бурштинова Зоря",
            "name_en": "Amber Dawn",
            "author_uk": "Т. Коваль",
            "author_en": "T. Koval",
            "description_uk": (
                "<p>Ранній сорт із жовтими, на сонці бурштиновими ягодами. Хрустка м'якоть "
                "з виразним мускатним ароматом.</p>"
            ),
            "description_en": (
                "<p>An early variety with yellow berries that turn amber in the sun. "
                "Crisp flesh with a distinct muscat aroma.</p>"
            ),
            "bunch_weight_min": _d("0.4"),
            "bunch_weight_max": _d("0.6"),
            "berry_weight_min": _d("6"),
            "berry_weight_max": _d("8"),
            "berry_size_min": _d("20"),
            "berry_size_max": _d("24"),
            "disease_susceptibility_min": _d("3"),
            "disease_susceptibility_max": _d("3.5"),
            "frost_resistance": -21,
            "cutting_price": _d("25"),
            "cutting_available": True,
            "sapling_price": _d("100"),
            "sapling_available": False,
        },
        dictionaries={
            "ripening": "rannii",
            "berry_color": "zhovtyi",
            "pulp": "khrustka",
            "taste": "muskatnyi",
            "vigor": "serednorosla",
        },
        photo_count=4,
    ),
    DemoVariety(
        slug="stepovyi-rubin",
        # No English texts on purpose: the API must fall back to Ukrainian.
        fields={
            "name_uk": "Степовий Рубін",
            "alt_names_uk": "Рубін степовий",
            "description_uk": (
                "<p>Сорт середнього терміну дозрівання з червоними округлими ягодами. "
                "Невибагливий, добре переносить посуху.</p>"
            ),
            "bunch_weight_min": _d("0.7"),
            "bunch_weight_max": _d("1.2"),
            "berry_weight_min": _d("7"),
            "berry_weight_max": _d("9"),
            "berry_size_min": _d("22"),
            "berry_size_max": _d("25"),
            "disease_susceptibility_min": _d("2"),
            "disease_susceptibility_max": _d("2.5"),
            "frost_resistance": -24,
            "cutting_price": _d("35"),
            "cutting_available": False,
            "sapling_price": _d("140"),
            "sapling_available": True,
        },
        dictionaries={
            "ripening": "serednii",
            "berry_color": "chervonyi",
            "pulp": "sokovyta",
            "taste": "prostyi",
            "vigor": "duzhe-sylnorosla",
        },
        photo_count=3,
    ),
    DemoVariety(
        slug="nichnyi-sapfir",
        # Out of stock and without a description.
        fields={
            "name_uk": "Нічний Сапфір",
            "name_en": "Night Sapphire",
            "bunch_weight_min": _d("0.6"),
            "bunch_weight_max": _d("1"),
            "berry_weight_min": _d("10"),
            "berry_weight_max": _d("14"),
            "berry_size_min": _d("28"),
            "berry_size_max": _d("34"),
            "disease_susceptibility_min": _d("3.5"),
            "disease_susceptibility_max": _d("4"),
            "frost_resistance": -20,
            "cutting_price": _d("40"),
            "cutting_available": False,
            "sapling_price": _d("160"),
            "sapling_available": False,
        },
        dictionaries={
            "ripening": "piznii",
            "berry_color": "synii",
            "pulp": "miasysta",
            "taste": "duzhe-harmoniinyi",
            "vigor": "sylnorosla",
        },
        photo_count=3,
    ),
    DemoVariety(
        slug="bilyi-tuman",
        # No photos: the frontend must show its placeholder.
        fields={
            "name_uk": "Білий Туман",
            "name_en": "White Mist",
            "description_uk": (
                "<p>Ранньо-середній сорт з білими ягодами, вкритими густим восковим нальотом.</p>"
            ),
            "description_en": (
                "<p>An early-mid variety with white berries under a thick waxy bloom.</p>"
            ),
            "bunch_weight_min": _d("0.3"),
            "bunch_weight_max": _d("0.5"),
            "berry_weight_min": _d("4"),
            "berry_weight_max": _d("6"),
            "berry_size_min": _d("18"),
            "berry_size_max": _d("21"),
            "disease_susceptibility_min": _d("2"),
            "disease_susceptibility_max": _d("3"),
            "frost_resistance": -26,
            "cutting_price": _d("20"),
            "cutting_available": True,
            "sapling_price": _d("90"),
            "sapling_available": True,
        },
        dictionaries={
            "ripening": "ranno-serednii",
            "berry_color": "bilyi",
            "pulp": "sokovyta",
            "taste": "lehkyi-muskat",
            "vigor": "slaborosla",
        },
    ),
)

DEMO_SLUGS: tuple[str, ...] = tuple(item.slug for item in DEMO_VARIETIES)


@dataclass
class SeedReport:
    created: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    photos: int = 0


def find_photo_files(slug: str, photos_dir: Path = PHOTOS_DIR) -> list[Path]:
    """Own photos of a demo variety from `fixtures/demo/photos/<slug>/`, sorted by name."""
    folder = photos_dir / slug
    if not folder.is_dir():
        return []
    return sorted(
        path
        for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() in PHOTO_EXTENSIONS
    )


def placeholder_photo(title: str, berry_color: str, index: int) -> bytes:
    """
    Draw a JPEG placeholder: a grape bunch in the colour of the berries on a soft background.

    `index` varies the composition, so the photos of one variety differ from each other.
    """
    width, height = PLACEHOLDER_SIZE
    rng = random.Random(f"{title}-{index}")
    fill, shadow = BERRY_PALETTE.get(berry_color, DEFAULT_BERRY)

    image = Image.new("RGB", PLACEHOLDER_SIZE, (238 - index * 6, 236, 214 + index * 4))
    draw = ImageDraw.Draw(image)

    radius = 34 + rng.randint(-4, 8)
    cx = width // 2 + rng.randint(-160, 160)
    top = 230 + rng.randint(-40, 40)

    # Stem and leaf.
    draw.line([(cx, top - 20), (cx + 30, top - 120)], fill="#6b5a2e", width=12)
    draw.ellipse([cx + 20, top - 200, cx + 200, top - 90], fill="#6f9a45")

    # Berries: rows that narrow towards the tip of the bunch.
    rows = (5, 6, 5, 4, 3, 2, 1)
    step = radius * 1.7
    for row, count in enumerate(rows):
        y = top + row * step
        start = cx - (count - 1) * step / 2
        for column in range(count):
            x = start + column * step + rng.uniform(-6, 6)
            draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=shadow)
            draw.ellipse(
                [x - radius + 4, y - radius + 2, x + radius - 6, y + radius - 6], fill=fill
            )
            draw.ellipse(
                [x - radius * 0.5, y - radius * 0.6, x - radius * 0.1, y - radius * 0.2],
                fill="#ffffff",
            )

    font = ImageFont.load_default(size=44)
    draw.text((40, height - 90), f"{title} · demo {index}", fill="#4a4038", font=font)

    buffer = io.BytesIO()
    image.save(buffer, "JPEG", quality=85)
    return buffer.getvalue()


def _create_variety(item: DemoVariety) -> Variety:
    references = {
        name: DICTIONARIES[name].objects.get(slug=slug) for name, slug in item.dictionaries.items()
    }
    variety = Variety(slug=item.slug, **item.fields, **references)
    variety.full_clean()
    variety.save()
    return variety


def _add_photos(variety: Variety, item: DemoVariety, photos_dir: Path) -> int:
    files = find_photo_files(item.slug, photos_dir)
    if files:
        sources = [(path.name, path.read_bytes()) for path in files]
    else:
        title = item.fields.get("name_en") or item.slug.replace("-", " ").title()
        berry = item.dictionaries.get("berry_color", "")
        sources = [
            (f"{item.slug}-{index}.jpg", placeholder_photo(title, berry, index))
            for index in range(1, item.photo_count + 1)
        ]

    name_uk = item.fields["name_uk"]
    name_en = item.fields.get("name_en") or ""
    for order, (filename, content) in enumerate(sources):
        photo = VarietyPhoto(
            variety=variety,
            order=order,
            is_main=order == 0,
            alt_uk=f"{name_uk}, фото {order + 1}",
            alt_en=f"{name_en}, photo {order + 1}" if name_en else None,
        )
        photo.image.save(filename, ContentFile(content), save=False)
        photo.save()
    return len(sources)


def _add_videos(variety: Variety, item: DemoVariety) -> None:
    for order, video in enumerate(item.videos):
        VarietyVideo.objects.create(
            variety=variety,
            youtube_url=video.youtube_url,
            title_uk=video.title_uk,
            title_en=video.title_en,
            order=order,
        )


def seed_varieties(photos_dir: Path = PHOTOS_DIR) -> SeedReport:
    """
    Create the demo varieties with photos and videos.

    Idempotent by slug: a variety that already exists is left untouched, so admin edits survive.
    """
    report = SeedReport()
    for item in DEMO_VARIETIES:
        if Variety.objects.filter(slug=item.slug).exists():
            report.skipped.append(item.slug)
            continue
        with transaction.atomic():
            variety = _create_variety(item)
            report.photos += _add_photos(variety, item, photos_dir)
            _add_videos(variety, item)
        report.created.append(item.slug)
    return report


def delete_demo_varieties() -> int:
    """Delete the demo varieties (with their photos and videos); other varieties stay."""
    _total, per_model = Variety.objects.filter(slug__in=DEMO_SLUGS).delete()
    return per_model.get(Variety._meta.label, 0)
