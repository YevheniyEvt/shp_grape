"""
Default values of the catalog reference lists (uk + en).

The values are frozen here on purpose: slugs are written explicitly (historical models have no
custom `save()`), and later changes of the code must not change what this migration creates.
Existing rows with the same slug are left untouched, so admin edits survive re-running it.
"""

from django.db import migrations

# model name -> [(slug, Ukrainian name, English name)] in display order
DEFAULTS = {
    "RipeningPeriod": [
        ("duzhe-rannii", "Дуже ранній", "Very early"),
        ("rannii", "Ранній", "Early"),
        ("ranno-serednii", "Ранньо-середній", "Early-mid"),
        ("serednii", "Середній", "Mid-season"),
        ("seredno-piznii", "Середньо-пізній", "Mid-late"),
        ("piznii", "Пізній", "Late"),
        ("duzhe-piznii", "Дуже пізній", "Very late"),
    ],
    "BerryColor": [
        ("bilyi", "Білий", "White"),
        ("zhovtyi", "Жовтий", "Yellow"),
        ("rozhevyi", "Рожевий", "Pink"),
        ("chervonyi", "Червоний", "Red"),
        ("fioletovyi", "Фіолетовий", "Purple"),
        ("synii", "Синій", "Blue"),
        ("chornyi", "Чорний", "Black"),
    ],
    "PulpConsistency": [
        ("sokovyta", "Соковита", "Juicy"),
        ("miasysto-sokovyta", "М’ясисто-соковита", "Fleshy and juicy"),
        ("miasysta", "М’ясиста", "Fleshy"),
        ("khrustka", "Хрустка", "Crisp"),
    ],
    "Taste": [
        ("prostyi", "Простий", "Simple"),
        ("harmoniinyi", "Гармонійний", "Harmonious"),
        ("duzhe-harmoniinyi", "Дуже гармонійний", "Very harmonious"),
        ("lehkyi-muskat", "Легкий мускат", "Light muscat"),
        ("muskatnyi", "Мускатний", "Muscat"),
        ("izabelnyi", "Ізабельний", "Foxy (Isabella)"),
    ],
    "GrowthVigor": [
        ("slaborosla", "Слаборосла", "Low vigour"),
        ("serednorosla", "Середньоросла", "Medium vigour"),
        ("sylnorosla", "Сильноросла", "Vigorous"),
        ("duzhe-sylnorosla", "Дуже сильноросла", "Very vigorous"),
    ],
}


def create_defaults(apps, schema_editor):
    for model_name, rows in DEFAULTS.items():
        model = apps.get_model("catalog", model_name)
        for order, (slug, name_uk, name_en) in enumerate(rows, start=1):
            model.objects.get_or_create(
                slug=slug,
                defaults={"name": name_uk, "name_uk": name_uk, "name_en": name_en, "order": order},
            )


def remove_unused_defaults(apps, schema_editor):
    for model_name, rows in DEFAULTS.items():
        model = apps.get_model("catalog", model_name)
        slugs = [slug for slug, _name_uk, _name_en in rows]
        model.objects.filter(slug__in=slugs, varieties__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0002_photo_main_and_slug_help"),
    ]

    operations = [
        migrations.RunPython(create_defaults, remove_unused_defaults),
    ]
