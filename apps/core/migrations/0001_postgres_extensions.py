"""Enable PostgreSQL extensions used for fuzzy and accent-insensitive search."""

from django.contrib.postgres.operations import TrigramExtension, UnaccentExtension
from django.db import migrations


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        TrigramExtension(),
        UnaccentExtension(),
    ]
