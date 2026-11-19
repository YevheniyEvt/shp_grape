"""
Default content (uk + en): site name of the settings row and the "About us" page.

Values are frozen here on purpose. Existing values are left untouched, so admin edits survive
re-running the migration; the reverse removes only what is still unchanged.
"""

from django.db import migrations

SITE_NAME = {"uk": "Виноградник", "en": "Vineyard"}
ABOUT_SLUG = "about"
ABOUT = {
    "title_uk": "Про нас",
    "title_en": "About us",
    "body_uk": "<p>Розкажіть тут про свій виноградник: історію, сорти й підхід до вирощування.</p>",
    "body_en": "<p>Tell visitors about your vineyard here: its story, varieties and approach.</p>",
}


def create_defaults(apps, schema_editor):
    SiteSettings = apps.get_model("content", "SiteSettings")
    settings, _created = SiteSettings.objects.get_or_create(pk=1)
    changed = []
    for code, name in SITE_NAME.items():
        field = f"site_name_{code}"
        if not getattr(settings, field):
            setattr(settings, field, name)
            changed.append(field)
    if changed:
        settings.save(update_fields=changed)

    Page = apps.get_model("content", "Page")
    Page.objects.get_or_create(slug=ABOUT_SLUG, defaults={"title": ABOUT["title_uk"], **ABOUT})


def remove_defaults(apps, schema_editor):
    Page = apps.get_model("content", "Page")
    Page.objects.filter(slug=ABOUT_SLUG, body_uk=ABOUT["body_uk"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0003_site_settings_fields_and_content"),
    ]

    operations = [
        migrations.RunPython(create_defaults, remove_defaults),
    ]
