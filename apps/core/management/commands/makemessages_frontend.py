"""Extract frontend UI strings (`t`, `nt`, `pt` calls) into `djangojs.po` catalogs."""

from pathlib import Path

import polib
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.core.i18n import (
    DEFAULT_PLURAL_FORMS,
    extract_from_directory,
    merge_catalog,
    new_catalog,
)


def plural_forms_for(locale_dir: Path) -> str:
    """Reuse the Plural-Forms header of the language's `django.po`, if present."""
    django_po = locale_dir / "LC_MESSAGES" / "django.po"
    if django_po.exists():
        return polib.pofile(str(django_po)).metadata.get("Plural-Forms", DEFAULT_PLURAL_FORMS)
    return DEFAULT_PLURAL_FORMS


class Command(BaseCommand):
    help = (
        "Scan the Next.js sources for t()/nt()/pt() calls and update "
        "locale/<lang>/LC_MESSAGES/djangojs.po for every language in settings.LANGUAGES."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            default=str(settings.BASE_DIR / "frontend" / "src"),
            help="Frontend source directory to scan.",
        )
        parser.add_argument(
            "--check",
            action="store_true",
            help="Do not write files; fail if any catalog is out of date.",
        )

    def handle(self, *args, **options):
        source = Path(options["source"])
        if not source.is_dir():
            raise CommandError(f"Source directory not found: {source}")

        messages, warnings = extract_from_directory(source, relative_to=settings.BASE_DIR)
        for warning in warnings:
            self.stderr.write(
                f"warning: non-literal translation call at {warning.path}:{warning.line}: "
                f"{warning.text}"
            )

        locale_root = Path(settings.LOCALE_PATHS[0])
        outdated: list[str] = []
        for code, _name in settings.LANGUAGES:
            locale_dir = locale_root / code
            po_path = locale_dir / "LC_MESSAGES" / "djangojs.po"
            if po_path.exists():
                current_text = po_path.read_text(encoding="utf-8")
                po = polib.pofile(current_text, wrapwidth=0)
            else:
                current_text = ""
                po = new_catalog(code, plural_forms_for(locale_dir))

            merged = merge_catalog(po, messages)
            new_text = merged.__unicode__()
            if new_text == current_text:
                continue
            outdated.append(po_path.relative_to(settings.BASE_DIR).as_posix())
            if not options["check"]:
                po_path.parent.mkdir(parents=True, exist_ok=True)
                # Always LF, so catalogs written on Windows match the repository.
                po_path.write_text(new_text, encoding="utf-8", newline="\n")

        if options["check"] and outdated:
            raise CommandError(
                "Frontend catalogs are out of date, run `just messages`: " + ", ".join(outdated)
            )
        self.stdout.write(
            self.style.SUCCESS(
                f"{len(messages)} frontend messages; updated: {', '.join(outdated) or 'nothing'}"
            )
        )
