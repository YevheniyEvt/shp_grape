from decimal import Decimal
from unittest import mock

import pytest
import time_machine
from django.db import IntegrityError

from apps.orders import services
from apps.orders.models import Order, PreOrder
from apps.orders.selectors import CartItem, Problem
from apps.orders.tests.factories import OrderFactory

pytestmark = pytest.mark.django_db

CUSTOMER = {"full_name": "Іван Тестовий", "phone": "+380501234567", "email": "ivan@example.com"}


def test_new_order_number_format():
    with time_machine.travel("2026-11-23 12:00 +02:00"):
        number = services.new_order_number()
    prefix, suffix = number.split("-")
    assert prefix == "261123"
    assert 1000 <= int(suffix) <= 9999


def test_place_order_snapshots_names_and_prices(variety, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks() as callbacks:
        order = services.place_order(
            CUSTOMER,
            [CartItem("rubin", "cutting", 3, Decimal("30.00")), CartItem("rubin", "sapling", 1)],
            "en",
        )
    assert len(callbacks) == 1
    order.refresh_from_db()
    assert order.status == Order.Status.NEW
    assert order.language == "en"
    assert order.total == Decimal("210.00")
    items = list(order.items.all())
    assert [(i.variety_name, i.kind, i.quantity, i.unit_price) for i in items] == [
        ("Ruby", "cutting", 3, Decimal("30.00")),
        ("Ruby", "sapling", 1, Decimal("120.00")),
    ]

    # Later catalog changes do not touch the order.
    variety.sapling_price = Decimal("999")
    variety.name_en = "Renamed"
    variety.save()
    item = order.items.get(kind="sapling")
    assert (item.variety_name, item.unit_price) == ("Ruby", Decimal("120.00"))
    variety.delete()
    item.refresh_from_db()
    assert item.variety is None
    assert item.variety_name == "Ruby"


def test_place_order_merges_repeated_items(variety):
    order = services.place_order(
        CUSTOMER, [CartItem("rubin", "cutting", 2), CartItem("rubin", "cutting", 3)], "uk"
    )
    [item] = order.items.all()
    assert item.quantity == 5
    assert item.variety_name == "Рубін"
    assert order.total == Decimal("150.00")


@pytest.mark.parametrize(
    ("item", "problem"),
    [
        (CartItem("sapfir", "cutting", 1), Problem.UNAVAILABLE),
        (CartItem("sapfir", "sapling", 1), Problem.UNAVAILABLE),
        (CartItem("missing", "cutting", 1), Problem.NOT_FOUND),
        (CartItem("rubin", "cutting", 1, Decimal("25.00")), Problem.PRICE_CHANGED),
    ],
)
def test_place_order_rejects_problems(variety, sold_out, item, problem):
    with pytest.raises(services.OrderRejected) as error:
        services.place_order(CUSTOMER, [CartItem("rubin", "sapling", 1), item], "uk")
    assert [line.problem for line in error.value.lines] == [None, problem]
    assert "1 item(s)" in str(error.value)
    assert not Order.objects.exists()


def test_order_number_retries_on_collision(variety):
    OrderFactory(number="261123-1111")
    numbers = ["261123-1111", "261123-2222"]
    with mock.patch.object(services, "new_order_number", side_effect=numbers):
        order = services.place_order(CUSTOMER, [CartItem("rubin", "cutting", 1)], "uk")
    assert order.number == "261123-2222"


def test_order_number_gives_up(variety):
    OrderFactory(number="261123-1111")
    with (
        mock.patch.object(services, "new_order_number", return_value="261123-1111"),
        pytest.raises(RuntimeError),
    ):
        services.place_order(CUSTOMER, [CartItem("rubin", "cutting", 1)], "uk")
    assert Order.objects.count() == 1


def test_order_save_reraises_other_integrity_errors(variety):
    with (
        mock.patch.object(Order, "save", side_effect=IntegrityError("other")),
        pytest.raises(IntegrityError),
    ):
        services.place_order(CUSTOMER, [CartItem("rubin", "cutting", 1)], "uk")


def test_create_preorder_and_message(django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks() as callbacks:
        preorder = services.create_preorder(
            {"full_name": "Оля", "phone": "+380501234567", "description": "Рубін, 5 саджанців"},
            "en",
        )
        message = services.create_contact_message(
            {"name": "Оля", "email": "olia@example.com", "subject": "", "message": "Привіт"}, "uk"
        )
    assert len(callbacks) == 2
    assert preorder.language == "en"
    assert preorder.status == PreOrder.Status.NEW
    assert message.language == "uk"
    assert not message.is_processed


def test_set_status():
    orders = [OrderFactory(), OrderFactory(), OrderFactory(status=Order.Status.DONE)]
    changed = services.set_status(Order.objects.all(), Order.Status.DONE)
    assert changed == 2
    assert set(Order.objects.values_list("status", flat=True)) == {"done"}
    assert len(orders) == 3
