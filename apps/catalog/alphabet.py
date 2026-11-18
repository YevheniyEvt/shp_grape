"""Alphabet helpers for the "browse by letter" navigation."""

from collections.abc import Iterable

# Group used for names that start with a digit, e.g. breeding codes like `12-34`.
DIGITS_GROUP = "#"

ALPHABETS: dict[str, str] = {
    "uk": "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ",
    "en": "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
}


def first_letter(name: str | None) -> str:
    """
    Return the navigation letter of a name: its first letter in upper case.

    Leading quotes and punctuation are skipped; names starting with a digit fall into `#`.
    """
    for char in name or "":
        if char.isalpha():
            return char.upper()
        if char.isdigit():
            return DIGITS_GROUP
    return ""


def sort_letters(letters: Iterable[str], language: str) -> list[str]:
    """
    Sort letters in the order of the language's alphabet.

    Letters outside the alphabet follow it in code-point order, and the digits group comes last.
    """
    alphabet = ALPHABETS.get(language, "")

    def key(letter: str) -> tuple[int, int, str]:
        if letter == DIGITS_GROUP:
            return (2, 0, letter)
        position = alphabet.find(letter)
        if position >= 0:
            return (0, position, letter)
        return (1, 0, letter)

    return sorted({letter for letter in letters if letter}, key=key)
