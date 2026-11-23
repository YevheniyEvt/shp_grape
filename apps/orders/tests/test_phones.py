import pytest

from apps.orders.phones import normalize_phone


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("050 123 45 67", "+380501234567"),
        ("(050) 123-45-67", "+380501234567"),
        ("+38 (050) 123-45-67", "+380501234567"),
        ("380501234567", "+380501234567"),
        (" +380501234567 ", "+380501234567"),
        ("+48 512 345 678", "+48512345678"),
        ("+1 202 555 0143", "+12025550143"),
    ],
)
def test_valid_phones(raw, expected):
    assert normalize_phone(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "abc",
        "123",
        "50 123 45 67",  # local number without the leading 0
        "+380 50 123 45",  # too short
        "+3805012345678",  # too long for Ukraine
        "48512345678",  # foreign number without +
        "+1234",
        "+1234567890123456",
    ],
)
def test_invalid_phones(raw):
    assert normalize_phone(raw) is None
