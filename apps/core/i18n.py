"""
Extraction of frontend UI strings into Django's `djangojs.po` catalogs.

The Next.js frontend marks translatable strings with `t("...")`, `nt("one", "many", n)`
and `pt("context", "...")`. Django's `makemessages` cannot parse TSX with these keywords,
so this module scans the sources itself and merges the result into
`locale/<lang>/LC_MESSAGES/djangojs.po` with polib, keeping existing translations.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import polib

SOURCE_SUFFIXES = (".ts", ".tsx", ".js", ".jsx")
EXCLUDED_PARTS = ("node_modules", ".next", "__tests__")
EXCLUDED_SUFFIXES = (".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx", ".d.ts")

# Number of leading string arguments each keyword takes.
KEYWORD_ARITY = {"t": 1, "nt": 2, "pt": 2}

_CALL_RE = re.compile(r"(?<![\w$.])(t|nt|pt)\(\s*")
_STRING_RE = re.compile(r"\"((?:[^\"\\\n]|\\.)*)\"|'((?:[^'\\\n]|\\.)*)'")
_SEPARATOR_RE = re.compile(r"\s*,\s*")
_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"', "'": "'", "`": "`"}
_ESCAPE_RE = re.compile(r"\\(u\{[0-9a-fA-F]+\}|u[0-9a-fA-F]{4}|.)")

DEFAULT_PLURAL_FORMS = "nplurals=2; plural=(n != 1);"


@dataclass(frozen=True)
class MessageKey:
    """Identity of a gettext message."""

    msgid: str
    msgctxt: str | None = None
    msgid_plural: str | None = None


@dataclass
class ExtractedMessage:
    key: MessageKey
    occurrences: list[tuple[str, int]] = field(default_factory=list)


@dataclass(frozen=True)
class ExtractionWarning:
    path: str
    line: int
    text: str


def unescape_js(value: str) -> str:
    """Decode JavaScript string escapes (`\\n`, `\\"`, `\\u0041`, `\\u{1F600}`)."""

    def replace(match: re.Match[str]) -> str:
        token = match.group(1)
        if token.startswith("u{"):
            return chr(int(token[2:-1], 16))
        if token.startswith("u") and len(token) == 5:
            return chr(int(token[1:], 16))
        return _ESCAPES.get(token, token)

    return _ESCAPE_RE.sub(replace, value)


def _read_string_args(source: str, start: int, count: int) -> list[str] | None:
    """Read `count` comma-separated string literals starting at `start`."""
    values: list[str] = []
    position = start
    for index in range(count):
        if index:
            separator = _SEPARATOR_RE.match(source, position)
            if not separator:
                return None
            position = separator.end()
        literal = _STRING_RE.match(source, position)
        if not literal:
            return None
        raw = literal.group(1) if literal.group(1) is not None else literal.group(2)
        values.append(unescape_js(raw))
        position = literal.end()
    return values


def extract_from_source(
    source: str, path: str = "<string>"
) -> tuple[list[ExtractedMessage], list[ExtractionWarning]]:
    """Find translatable calls in one source file."""
    messages: list[ExtractedMessage] = []
    warnings: list[ExtractionWarning] = []
    for match in _CALL_RE.finditer(source):
        keyword = match.group(1)
        line = source.count("\n", 0, match.start()) + 1
        args = _read_string_args(source, match.end(), KEYWORD_ARITY[keyword])
        if args is None:
            snippet = source[match.start() : match.end() + 40].splitlines()[0]
            warnings.append(ExtractionWarning(path=path, line=line, text=snippet))
            continue
        if keyword == "t":
            key = MessageKey(msgid=args[0])
        elif keyword == "nt":
            key = MessageKey(msgid=args[0], msgid_plural=args[1])
        else:
            key = MessageKey(msgid=args[1], msgctxt=args[0])
        if not key.msgid:
            continue
        messages.append(ExtractedMessage(key=key, occurrences=[(path, line)]))
    return messages, warnings


def iter_source_files(root: Path) -> Iterable[Path]:
    """Yield frontend source files that may contain UI strings."""
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix not in SOURCE_SUFFIXES:
            continue
        if any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        if path.name.endswith(EXCLUDED_SUFFIXES):
            continue
        yield path


def extract_from_directory(
    root: Path, relative_to: Path | None = None
) -> tuple[dict[MessageKey, ExtractedMessage], list[ExtractionWarning]]:
    """Extract and de-duplicate messages from all source files under `root`."""
    collected: dict[MessageKey, ExtractedMessage] = {}
    warnings: list[ExtractionWarning] = []
    base = relative_to or root
    for path in iter_source_files(root):
        display = path.relative_to(base).as_posix()
        messages, file_warnings = extract_from_source(path.read_text(encoding="utf-8"), display)
        warnings.extend(file_warnings)
        for message in messages:
            existing = collected.get(message.key)
            if existing:
                existing.occurrences.extend(message.occurrences)
            else:
                collected[message.key] = message
    return collected, warnings


def nplurals_from_header(plural_forms: str) -> int:
    """Parse `nplurals` from a Plural-Forms header (defaults to 2)."""
    match = re.search(r"nplurals\s*=\s*(\d+)", plural_forms or "")
    return int(match.group(1)) if match else 2


def new_catalog(language: str, plural_forms: str) -> polib.POFile:
    """Create an empty catalog with a clean header."""
    po = polib.POFile(wrapwidth=0)
    po.metadata = {
        "Project-Id-Version": "shp_grape",
        "Language": language,
        "MIME-Version": "1.0",
        "Content-Type": "text/plain; charset=UTF-8",
        "Content-Transfer-Encoding": "8bit",
        "Plural-Forms": plural_forms,
    }
    return po


def merge_catalog(po: polib.POFile, messages: dict[MessageKey, ExtractedMessage]) -> polib.POFile:
    """
    Return a new catalog with exactly `messages` as active entries.

    Existing translations are kept; messages no longer in the sources become
    obsolete (translations preserved), and returning messages are revived.
    """
    nplurals = nplurals_from_header(po.metadata.get("Plural-Forms", DEFAULT_PLURAL_FORMS))
    existing = {(entry.msgctxt, entry.msgid): entry for entry in po}

    merged = polib.POFile(wrapwidth=0)
    merged.metadata = dict(po.metadata)
    merged.metadata_is_fuzzy = False

    for key in sorted(messages, key=lambda k: (k.msgid.lower(), k.msgctxt or "")):
        message = messages[key]
        previous = existing.pop((key.msgctxt, key.msgid), None)
        entry = polib.POEntry(
            msgid=key.msgid,
            msgctxt=key.msgctxt,
            # File-only references (like `makemessages --add-location=file`): line numbers
            # would make catalogs stale after any reformatting.
            occurrences=[(path, "") for path in sorted({path for path, _ in message.occurrences})],
        )
        if key.msgid_plural:
            entry.msgid_plural = key.msgid_plural
            forms = previous.msgstr_plural if previous and previous.msgstr_plural else {}
            entry.msgstr_plural = {i: forms.get(i, "") for i in range(nplurals)}
        else:
            entry.msgstr = previous.msgstr if previous else ""
        if previous and "fuzzy" in previous.flags:
            entry.flags.append("fuzzy")
        merged.append(entry)

    for previous in sorted(existing.values(), key=lambda e: e.msgid.lower()):
        if previous.translated() or previous.obsolete:
            previous.obsolete = True
            previous.occurrences = []
            merged.append(previous)
    return merged
