from pathlib import Path

import polib
import pytest
from django.core.management import CommandError, call_command
from hypothesis import given
from hypothesis import strategies as st

from apps.core.i18n import (
    ExtractedMessage,
    MessageKey,
    extract_from_directory,
    extract_from_source,
    iter_source_files,
    merge_catalog,
    new_catalog,
    nplurals_from_header,
    unescape_js,
)

UK_PLURAL_FORMS = (
    "nplurals=4; plural=(n % 1 == 0 && n % 10 == 1 && n % 100 != 11 ? 0 : "
    "n % 1 == 0 && n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 12 || n % 100 > 14) ? 1 : 2);"
)


def keys(source: str) -> list[MessageKey]:
    messages, _warnings = extract_from_source(source)
    return [message.key for message in messages]


# --- extraction -------------------------------------------------------------


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ('t("Catalog")', [MessageKey("Catalog")]),
        ("t('Catalog')", [MessageKey("Catalog")]),
        ('{t("Cart")}', [MessageKey("Cart")]),
        ('const { t } = useT(); t( "Spaced" )', [MessageKey("Spaced")]),
        (
            'nt("%(count)s variety", "%(count)s varieties", n)',
            [MessageKey("%(count)s variety", msgid_plural="%(count)s varieties")],
        ),
        ('pt("month", "May")', [MessageKey("May", msgctxt="month")]),
        ('t("Hello %(name)s", { name })', [MessageKey("Hello %(name)s")]),
    ],
)
def test_extracts_keyword_calls(source, expected):
    assert keys(source) == expected


@pytest.mark.parametrize(
    "source",
    [
        'split("x")',  # keyword must be a whole identifier
        'obj.t("x")',  # method calls are not the translator
        "$t('x')",
        't("")',  # empty msgid is ignored
    ],
)
def test_ignores_non_translator_calls(source):
    assert keys(source) == []


def test_reports_non_literal_calls_as_warnings():
    messages, warnings = extract_from_source("const a = 1;\nt(label)\nt(`x`)", path="a.tsx")

    assert messages == []
    assert [(w.path, w.line) for w in warnings] == [("a.tsx", 2), ("a.tsx", 3)]


def test_records_line_numbers():
    messages, _ = extract_from_source('\n\nt("Third line")', path="page.tsx")

    assert messages[0].occurrences == [("page.tsx", 3)]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (r"Don\'t", "Don't"),
        (r"Say \"hi\"", 'Say "hi"'),
        (r"Line\nbreak", "Line\nbreak"),
        ("\\u0410", chr(0x0410)),
        (r"\u{1F347}", "\U0001f347"),
        (r"back\\slash", "back\\slash"),
    ],
)
def test_unescape_js(raw, expected):
    assert unescape_js(raw) == expected


def test_extracts_escaped_quotes_inside_literal():
    assert keys(r't("Say \"hi\"")') == [MessageKey('Say "hi"')]


@given(st.text(alphabet=st.characters(blacklist_characters='"\\\n\r'), min_size=1))
def test_any_simple_double_quoted_literal_round_trips(text):
    assert keys(f't("{text}")') == [MessageKey(text)]


def test_extract_from_directory_merges_duplicates_and_skips_tests(tmp_path: Path):
    src = tmp_path / "src"
    (src / "app").mkdir(parents=True)
    (src / "node_modules").mkdir()
    (src / "app" / "a.tsx").write_text('t("Catalog")', encoding="utf-8")
    (src / "app" / "b.ts").write_text('t("Catalog"); t("Cart")', encoding="utf-8")
    (src / "app" / "a.test.tsx").write_text('t("From test")', encoding="utf-8")
    (src / "node_modules" / "lib.js").write_text('t("Vendor")', encoding="utf-8")
    (src / "app" / "styles.css").write_text('t("Not code")', encoding="utf-8")

    messages, warnings = extract_from_directory(src, relative_to=tmp_path)

    assert set(messages) == {MessageKey("Catalog"), MessageKey("Cart")}
    assert messages[MessageKey("Catalog")].occurrences == [
        ("src/app/a.tsx", 1),
        ("src/app/b.ts", 1),
    ]
    assert warnings == []
    assert [p.name for p in iter_source_files(src)] == ["a.tsx", "b.ts"]


# --- merging ----------------------------------------------------------------


def _messages(*keys_: MessageKey) -> dict[MessageKey, ExtractedMessage]:
    return {key: ExtractedMessage(key=key, occurrences=[("x.tsx", 1)]) for key in keys_}


@pytest.mark.parametrize(
    ("header", "expected"),
    [(UK_PLURAL_FORMS, 4), ("nplurals=2; plural=(n != 1);", 2), ("", 2)],
)
def test_nplurals_from_header(header, expected):
    assert nplurals_from_header(header) == expected


def test_merge_adds_new_messages_with_empty_translations():
    po = new_catalog("uk", UK_PLURAL_FORMS)

    merged = merge_catalog(po, _messages(MessageKey("Cart"), MessageKey("a", msgid_plural="b")))

    cart = merged.find("Cart")
    plural = merged.find("a")
    assert cart.msgstr == ""
    assert plural.msgid_plural == "b"
    assert plural.msgstr_plural == {0: "", 1: "", 2: "", 3: ""}


def test_merge_keeps_existing_translations():
    po = new_catalog("uk", UK_PLURAL_FORMS)
    po.append(polib.POEntry(msgid="Cart", msgstr="Кошик"))

    merged = merge_catalog(po, _messages(MessageKey("Cart")))

    assert merged.find("Cart").msgstr == "Кошик"


def test_merge_keeps_context_entries_separate():
    po = new_catalog("uk", UK_PLURAL_FORMS)
    po.append(polib.POEntry(msgid="May", msgctxt="month", msgstr="Травень"))

    merged = merge_catalog(po, _messages(MessageKey("May", msgctxt="month"), MessageKey("May")))

    by_context = {(e.msgctxt, e.msgid): e.msgstr for e in merged}
    assert by_context == {("month", "May"): "Травень", (None, "May"): ""}


def test_merge_marks_removed_translated_messages_obsolete_and_drops_untranslated():
    po = new_catalog("uk", UK_PLURAL_FORMS)
    po.append(polib.POEntry(msgid="Old translated", msgstr="Старе"))
    po.append(polib.POEntry(msgid="Old empty", msgstr=""))

    merged = merge_catalog(po, _messages(MessageKey("Cart")))

    old = merged.find("Old translated", include_obsolete_entries=True)
    assert old.obsolete
    assert old.msgstr == "Старе"
    assert merged.find("Old empty", include_obsolete_entries=True) is None


def test_merge_revives_obsolete_message_that_returns():
    po = new_catalog("uk", UK_PLURAL_FORMS)
    po.append(polib.POEntry(msgid="Cart", msgstr="Кошик", obsolete=True))

    merged = merge_catalog(po, _messages(MessageKey("Cart")))

    cart = merged.find("Cart")
    assert cart is not None
    assert not cart.obsolete
    assert cart.msgstr == "Кошик"


def test_merge_preserves_fuzzy_flag_and_header_is_not_fuzzy():
    po = new_catalog("uk", UK_PLURAL_FORMS)
    po.metadata_is_fuzzy = True
    po.append(polib.POEntry(msgid="Cart", msgstr="Кошик", flags=["fuzzy"]))

    merged = merge_catalog(po, _messages(MessageKey("Cart")))

    assert "fuzzy" in merged.find("Cart").flags
    assert not merged.metadata_is_fuzzy


def test_merge_writes_unique_file_references_without_line_numbers():
    key = MessageKey("Cart")
    messages = {
        key: ExtractedMessage(key=key, occurrences=[("b.tsx", 9), ("a.tsx", 3), ("b.tsx", 1)])
    }

    merged = merge_catalog(new_catalog("uk", UK_PLURAL_FORMS), messages)

    assert merged.find("Cart").occurrences == [("a.tsx", ""), ("b.tsx", "")]
    assert "#: a.tsx b.tsx\n" in merged.__unicode__()


def test_command_output_does_not_change_when_lines_shift(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    page = src / "page.tsx"
    page.write_text('t("Cart")', encoding="utf-8")
    first, _ = extract_from_directory(src)
    page.write_text('\n\n\nt("Cart")', encoding="utf-8")
    second, _ = extract_from_directory(src)

    catalog = new_catalog("uk", UK_PLURAL_FORMS)
    assert (
        merge_catalog(catalog, first).__unicode__() == merge_catalog(catalog, second).__unicode__()
    )


def test_merge_sorts_entries_for_stable_diffs():
    po = new_catalog("uk", UK_PLURAL_FORMS)

    merged = merge_catalog(po, _messages(MessageKey("b"), MessageKey("A"), MessageKey("c")))

    assert [entry.msgid for entry in merged] == ["A", "b", "c"]


# --- management command -----------------------------------------------------


@pytest.fixture
def project(tmp_path: Path, settings):
    """A throwaway project tree with a frontend source dir and locale dir."""
    settings.BASE_DIR = tmp_path
    settings.LOCALE_PATHS = [tmp_path / "locale"]
    settings.LANGUAGES = [("uk", "Ukrainian"), ("en", "English")]
    src = tmp_path / "frontend" / "src"
    src.mkdir(parents=True)
    (src / "page.tsx").write_text('t("Catalog")', encoding="utf-8")
    django_po = tmp_path / "locale" / "uk" / "LC_MESSAGES" / "django.po"
    django_po.parent.mkdir(parents=True)
    django_po.write_text(
        f'msgid ""\nmsgstr ""\n"Plural-Forms: {UK_PLURAL_FORMS}\\n"\n', encoding="utf-8"
    )
    return tmp_path


def test_command_creates_catalog_per_language(project: Path):
    call_command("makemessages_frontend", source=str(project / "frontend" / "src"))

    uk = polib.pofile(str(project / "locale" / "uk" / "LC_MESSAGES" / "djangojs.po"))
    en = polib.pofile(str(project / "locale" / "en" / "LC_MESSAGES" / "djangojs.po"))
    assert uk.find("Catalog") is not None
    assert uk.metadata["Plural-Forms"] == UK_PLURAL_FORMS
    assert en.metadata["Plural-Forms"] == "nplurals=2; plural=(n != 1);"
    assert en.metadata["Language"] == "en"


def test_command_check_fails_when_catalogs_are_outdated(project: Path):
    source = str(project / "frontend" / "src")
    with pytest.raises(CommandError, match="out of date"):
        call_command("makemessages_frontend", source=source, check=True)

    call_command("makemessages_frontend", source=source)
    call_command("makemessages_frontend", source=source, check=True)  # now up to date


def test_command_is_idempotent(project: Path):
    source = str(project / "frontend" / "src")
    call_command("makemessages_frontend", source=source)
    po_path = project / "locale" / "uk" / "LC_MESSAGES" / "djangojs.po"
    first = po_path.read_text(encoding="utf-8")

    call_command("makemessages_frontend", source=source)

    assert po_path.read_text(encoding="utf-8") == first


def test_command_rejects_missing_source(project: Path):
    with pytest.raises(CommandError, match="not found"):
        call_command("makemessages_frontend", source=str(project / "missing"))


def test_command_warns_about_non_literal_calls(project: Path, capsys):
    (project / "frontend" / "src" / "bad.tsx").write_text("t(label)", encoding="utf-8")

    call_command("makemessages_frontend", source=str(project / "frontend" / "src"))

    assert "non-literal translation call" in capsys.readouterr().err
