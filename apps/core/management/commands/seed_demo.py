"""Fill the database with demo data: varieties with photos and videos, and an admin user."""

import os
from pathlib import Path

from django.core.management.base import BaseCommand, CommandParser

from apps.catalog import demo as catalog_demo
from apps.core.services import ensure_superuser


class Command(BaseCommand):
    help = (
        "Create demo data (idempotent by slug: existing objects are left untouched). "
        "Own photos are taken from fixtures/demo/photos/<variety-slug>/, otherwise placeholders "
        "are drawn."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete the demo objects first and create them again.",
        )
        parser.add_argument(
            "--photos-dir",
            type=Path,
            default=catalog_demo.PHOTOS_DIR,
            help="Folder with own demo photos, one subfolder per variety slug.",
        )

    def handle(self, *args, reset: bool, photos_dir: Path, **options) -> None:
        if reset:
            deleted = catalog_demo.delete_demo_varieties()
            self.stdout.write(f"Deleted demo varieties: {deleted}")

        report = catalog_demo.seed_varieties(photos_dir)
        self.stdout.write(
            self.style.SUCCESS(
                f"Varieties created: {len(report.created)}, photos: {report.photos}; "
                f"already present: {len(report.skipped)}"
            )
        )
        self._ensure_superuser()

    def _ensure_superuser(self) -> None:
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
        if not username or not password:
            self.stdout.write("Superuser skipped: set DJANGO_SUPERUSER_USERNAME and _PASSWORD.")
            return
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")
        if ensure_superuser(username, email, password):
            self.stdout.write(self.style.SUCCESS(f"Superuser created: {username}"))
        else:
            self.stdout.write(f"Superuser already exists: {username}")
