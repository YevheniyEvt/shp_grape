"""State-changing operations of the orders app."""

import secrets
from collections.abc import Sequence
from decimal import Decimal
from functools import partial
from typing import Any

from django.db import IntegrityError, transaction
from django.utils import timezone, translation

from apps.catalog.selectors import published_varieties
from apps.orders import emails
from apps.orders.models import ContactMessage, Order, OrderItem, PreOrder
from apps.orders.selectors import CartItem, CartLine, check_items

NUMBER_ATTEMPTS = 10


class OrderRejected(Exception):
    """Some items cannot be ordered: unknown, out of stock, or their price has changed."""

    def __init__(self, lines: Sequence[CartLine]) -> None:
        # All checked lines, so the client can refresh the whole cart.
        self.lines = list(lines)
        problems = sum(1 for line in lines if line.problem)
        super().__init__(f"{problems} item(s) cannot be ordered")


def new_order_number() -> str:
    """A short human-readable number: the date and four random digits, e.g. `261123-4821`."""
    return f"{timezone.localdate():%y%m%d}-{1000 + secrets.randbelow(9000)}"


def _save_with_number(order: Order) -> None:
    for _attempt in range(NUMBER_ATTEMPTS):
        order.number = new_order_number()
        try:
            with transaction.atomic():
                order.save()
        except IntegrityError:
            if Order.objects.filter(number=order.number).exists():
                continue
            raise
        return
    raise RuntimeError("Could not generate a unique order number")


@transaction.atomic
def place_order(customer: dict[str, Any], items: Sequence[CartItem], language: str) -> Order:
    """
    Create an order from cart items after checking them against the catalog.

    The varieties are locked until the transaction ends, so the price and availability the
    order is checked against cannot change halfway. Names and prices are copied into the items.
    Raises `OrderRejected` when any item is unknown, unavailable or has a different price.
    Emails are sent after the commit.
    """
    lines = check_items(items, published_varieties().select_for_update())
    if any(line.problem for line in lines):
        raise OrderRejected(lines)

    order = Order(**customer, language=language)
    order.total = sum((line.line_total for line in lines), Decimal(0))
    _save_with_number(order)
    with translation.override(language):
        OrderItem.objects.bulk_create(
            OrderItem(
                order=order,
                variety=line.variety,
                variety_name=line.variety.name,
                kind=line.item.kind,
                quantity=line.item.quantity,
                unit_price=line.price,
            )
            for line in lines
        )
    transaction.on_commit(partial(emails.send_order_emails, order.pk))
    return order


@transaction.atomic
def create_preorder(data: dict[str, Any], language: str) -> PreOrder:
    preorder = PreOrder.objects.create(**data, language=language)
    transaction.on_commit(partial(emails.send_preorder_email, preorder.pk))
    return preorder


@transaction.atomic
def create_contact_message(data: dict[str, Any], language: str) -> ContactMessage:
    message = ContactMessage.objects.create(**data, language=language)
    transaction.on_commit(partial(emails.send_contact_email, message.pk))
    return message


def set_status(queryset, status: str) -> int:
    """Change the status of the given orders or pre-orders (an admin action)."""
    return queryset.exclude(status=status).update(status=status, updated_at=timezone.now())
