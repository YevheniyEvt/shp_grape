from decimal import Decimal

import pytest

from apps.catalog.tests.factories import VarietyFactory, VarietyPhotoFactory
from apps.orders.models import MAX_ITEM_QUANTITY
from apps.orders.selectors import CartItem, Problem, cart_lines, merge_items, offer

pytestmark = pytest.mark.django_db


def test_merge_items_joins_repeated_products():
    items = [
        CartItem("a", "cutting", 2, Decimal("10")),
        CartItem("a", "sapling", 1),
        CartItem("a", "cutting", 3, Decimal("12")),
    ]
    assert merge_items(items) == [
        CartItem("a", "cutting", 5, Decimal("10")),
        CartItem("a", "sapling", 1),
    ]


def test_merge_items_caps_quantity():
    items = [CartItem("a", "cutting", MAX_ITEM_QUANTITY), CartItem("a", "cutting", 5)]
    assert merge_items(items)[0].quantity == MAX_ITEM_QUANTITY


def test_offer(variety, sold_out):
    assert offer(variety, "cutting") == (Decimal("30.00"), True)
    assert offer(variety, "sapling") == (Decimal("120.00"), True)
    assert offer(sold_out, "cutting") == (Decimal("40.00"), False)
    # In stock but without a price: cannot be ordered.
    assert offer(sold_out, "sapling") == (None, False)


def test_cart_lines_ok(variety):
    [line] = cart_lines([CartItem("rubin", "sapling", 2)])
    assert line.variety == variety
    assert line.price == Decimal("120.00")
    assert line.available
    assert line.problem is None
    assert line.line_total == Decimal("240.00")


def test_cart_lines_problems(variety, sold_out):
    VarietyFactory(slug="hidden", is_published=False, cutting_price=1, cutting_available=True)
    lines = cart_lines(
        [
            CartItem("rubin", "cutting", 1, Decimal("30.00")),
            CartItem("rubin", "sapling", 1, Decimal("100.00")),
            CartItem("sapfir", "cutting", 1),
            CartItem("hidden", "cutting", 1),
            CartItem("missing", "cutting", 1),
        ]
    )
    assert [line.problem for line in lines] == [
        None,
        Problem.PRICE_CHANGED,
        Problem.UNAVAILABLE,
        Problem.NOT_FOUND,
        Problem.NOT_FOUND,
    ]
    assert lines[1].price == Decimal("120.00")
    assert lines[3].line_total == 0


def test_cart_lines_constant_queries(django_assert_max_num_queries):
    for index in range(5):
        VarietyPhotoFactory(
            variety=VarietyFactory(slug=f"v{index}", cutting_price=10, cutting_available=True)
        )
    with django_assert_max_num_queries(2):
        lines = cart_lines([CartItem(f"v{index}", "cutting", 1) for index in range(5)])
        assert all(line.variety.card_photos for line in lines)
