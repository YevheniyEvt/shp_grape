"""Parsing and validation of YouTube video links."""

import re
from urllib.parse import parse_qs, urlparse

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

_VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
_WATCH_HOSTS = frozenset({"youtube.com", "m.youtube.com", "music.youtube.com"})
_EMBED_HOSTS = frozenset({"youtube.com", "m.youtube.com", "youtube-nocookie.com"})
_PATH_PREFIXES = ("embed", "shorts", "live", "v")


def parse_youtube_id(url: str) -> str | None:
    """
    Extract the 11-character video id from a YouTube link, or return None.

    Supported forms: `youtube.com/watch?v=ID`, `youtu.be/ID`, `youtube.com/embed/ID`,
    `youtube.com/shorts/ID`, `youtube.com/live/ID` and `youtube-nocookie.com/embed/ID`.
    """
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        return None
    host = (parsed.hostname or "").removeprefix("www.")
    parts = [part for part in parsed.path.split("/") if part]

    candidate: str | None = None
    if host == "youtu.be" and parts:
        candidate = parts[0]
    elif host in _WATCH_HOSTS and parts == ["watch"]:
        candidate = parse_qs(parsed.query).get("v", [None])[0]
    elif host in _EMBED_HOSTS and len(parts) >= 2 and parts[0] in _PATH_PREFIXES:
        candidate = parts[1]

    if candidate and _VIDEO_ID.match(candidate):
        return candidate
    return None


def validate_youtube_url(url: str) -> None:
    """Model/form validator: reject links that do not point to a YouTube video."""
    if parse_youtube_id(url) is None:
        raise ValidationError(
            _("Enter a link to a YouTube video."),
            code="invalid_youtube_url",
        )
