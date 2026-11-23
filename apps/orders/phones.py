"""Phone number normalisation for order forms."""

import re

_NON_DIGITS = re.compile(r"\D")


def normalize_phone(raw: str) -> str | None:
    """
    Return the phone in the international `+<digits>` form, or None when it is not valid.

    Ukrainian numbers may be written locally (`050 123 45 67`) or with the country code
    (`+38 (050) 123-45-67`, `380501234567`); foreign numbers need a leading `+`.
    """
    value = raw.strip()
    digits = _NON_DIGITS.sub("", value)
    if len(digits) == 10 and digits.startswith("0"):
        return f"+38{digits}"
    if len(digits) == 12 and digits.startswith("380"):
        return f"+{digits}"
    if value.startswith("+") and not digits.startswith("380") and 10 <= len(digits) <= 15:
        return f"+{digits}"
    return None
