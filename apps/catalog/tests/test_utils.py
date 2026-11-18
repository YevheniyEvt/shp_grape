import pytest
from django.core.exceptions import ValidationError

from apps.catalog.alphabet import first_letter, sort_letters
from apps.catalog.youtube import parse_youtube_id, validate_youtube_url

VIDEO_ID = "dQw4w9WgXcQ"


@pytest.mark.parametrize(
    "url",
    [
        f"https://www.youtube.com/watch?v={VIDEO_ID}",
        f"https://youtube.com/watch?v={VIDEO_ID}&t=42s",
        f"http://m.youtube.com/watch?feature=share&v={VIDEO_ID}",
        f"https://music.youtube.com/watch?v={VIDEO_ID}",
        f"https://youtu.be/{VIDEO_ID}",
        f"https://youtu.be/{VIDEO_ID}?si=abc",
        f"https://www.youtube.com/embed/{VIDEO_ID}",
        f"https://www.youtube-nocookie.com/embed/{VIDEO_ID}?rel=0",
        f"https://www.youtube.com/shorts/{VIDEO_ID}",
        f"https://www.youtube.com/live/{VIDEO_ID}",
        f"  https://youtu.be/{VIDEO_ID}  ",
    ],
)
def test_parse_youtube_id_supports_common_link_forms(url):
    assert parse_youtube_id(url) == VIDEO_ID


@pytest.mark.parametrize(
    "url",
    [
        "",
        "not a url",
        f"ftp://youtu.be/{VIDEO_ID}",
        f"https://vimeo.com/{VIDEO_ID}",
        "https://www.youtube.com/watch",
        "https://www.youtube.com/watch?v=short",
        "https://www.youtube.com/channel/UCabcdefghijk",
        "https://youtu.be/",
        f"https://evil-youtube.com/watch?v={VIDEO_ID}",
        f"https://www.youtube.com/watch?v={VIDEO_ID[:-1]}!",
    ],
)
def test_parse_youtube_id_rejects_other_links(url):
    assert parse_youtube_id(url) is None


def test_validate_youtube_url():
    validate_youtube_url(f"https://youtu.be/{VIDEO_ID}")
    with pytest.raises(ValidationError) as error:
        validate_youtube_url("https://vimeo.com/123")
    assert error.value.code == "invalid_youtube_url"


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("ранній", "Р"),
        ("Ювілейний", "Ю"),
        ("«Ґронка»", "Ґ"),
        ("12-34 (Тестовий)", "#"),
        ("early", "E"),
        ("", ""),
        (None, ""),
        ("---", ""),
    ],
)
def test_first_letter(name, expected):
    assert first_letter(name) == expected


def test_sort_letters_follows_ukrainian_alphabet():
    letters = ["Я", "#", "Ї", "І", "Ґ", "Г", "Є", "Е", "И", "Z", "", "Я"]
    assert sort_letters(letters, "uk") == ["Г", "Ґ", "Е", "Є", "И", "І", "Ї", "Я", "Z", "#"]


def test_sort_letters_for_english_and_unknown_language():
    assert sort_letters(["C", "#", "A", "Ж"], "en") == ["A", "C", "Ж", "#"]
    assert sort_letters(["B", "A"], "de") == ["A", "B"]
