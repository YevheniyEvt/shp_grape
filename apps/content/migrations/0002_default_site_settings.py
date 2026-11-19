"""
Default site settings row.

django-solo would create the row lazily, but the project rule is to ship defaults as data
migrations. An existing row is left untouched, so admin edits survive re-running it.
"""

from django.db import migrations

SINGLETON_ID = 1


def create_settings(apps, schema_editor):
    SiteSettings = apps.get_model("content", "SiteSettings")
    SiteSettings.objects.get_or_create(pk=SINGLETON_ID, defaults={"show_background": True})


def delete_unused_settings(apps, schema_editor):
    SiteSettings = apps.get_model("content", "SiteSettings")
    SiteSettings.objects.filter(pk=SINGLETON_ID, background_image="").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_settings, delete_unused_settings),
    ]
