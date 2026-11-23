"""
Demo orders, a pre-order and a contact message (`manage.py seed_demo`).

All people and contacts are invented. Demo orders have numbers starting with `DEMO-`; the pre-order
and the message use reserved `example.com` addresses, so they are found again and never mixed up
with real requests. No emails are sent.
"""

from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction

from apps.catalog.models import Variety
from apps.orders.models import ContactMessage, Order, OrderItem, PreOrder

DEMO_PREORDER_EMAIL = "demo-preorder@example.com"
DEMO_MESSAGE_EMAIL = "demo-message@example.com"


@dataclass(frozen=True)
class DemoItem:
    slug: str
    name: str
    kind: str
    quantity: int
    price: Decimal


DEMO_ORDERS: tuple[tuple[dict, tuple[DemoItem, ...]], ...] = (
    (
        {
            "number": "DEMO-0001",
            "full_name": "Андрій Тестовий",
            "phone": "+380000000010",
            "email": "demo-order1@example.com",
            "city": "Київ",
            "delivery_office": "Відділення № 1",
            "contact_method": "viber",
            "comment": "Зателефонуйте, будь ласка, після 18:00.",
            "status": Order.Status.NEW,
            "language": "uk",
        },
        (
            DemoItem("rankovyi-ametyst", "Ранковий Аметист", "cutting", 5, Decimal("30")),
            DemoItem("rankovyi-ametyst", "Ранковий Аметист", "sapling", 1, Decimal("120")),
            DemoItem("bilyi-tuman", "Білий Туман", "sapling", 2, Decimal("90")),
        ),
    ),
    (
        {
            "number": "DEMO-0002",
            "full_name": "Jane Doe",
            "phone": "+480000000020",
            "email": "demo-order2@example.com",
            "city": "Lviv",
            "delivery_office": "Parcel locker 2",
            "contact_method": "email",
            "status": Order.Status.SHIPPED,
            "language": "en",
            "admin_note": "Відправлено 2 листопада, ТТН 00000000000000.",
        },
        (DemoItem("burshtynova-zoria", "Amber Dawn", "cutting", 10, Decimal("25")),),
    ),
)

DEMO_PREORDER = {
    "full_name": "Марія Тестова",
    "phone": "+380000000030",
    "email": DEMO_PREORDER_EMAIL,
    "description": "Нічний Сапфір — 3 саджанці навесні, якщо з'являться.",
    "language": "uk",
}

DEMO_MESSAGE = {
    "name": "Петро Тестовий",
    "email": DEMO_MESSAGE_EMAIL,
    "subject": "Доставка за кордон",
    "message": "Добрий день! Чи відправляєте живці до Польщі?",
    "language": "uk",
}


@transaction.atomic
def seed_orders() -> list[str]:
    """Create the demo orders, pre-order and message that are missing; return what was created."""
    created = []
    varieties = Variety.objects.in_bulk(
        {item.slug for _fields, items in DEMO_ORDERS for item in items}, field_name="slug"
    )
    for fields, items in DEMO_ORDERS:
        if Order.objects.filter(number=fields["number"]).exists():
            continue
        order = Order.objects.create(
            **fields, total=sum((item.price * item.quantity for item in items), Decimal(0))
        )
        OrderItem.objects.bulk_create(
            OrderItem(
                order=order,
                variety=varieties.get(item.slug),
                variety_name=item.name,
                kind=item.kind,
                quantity=item.quantity,
                unit_price=item.price,
            )
            for item in items
        )
        created.append(order.number)
    if not PreOrder.objects.filter(email=DEMO_PREORDER_EMAIL).exists():
        PreOrder.objects.create(**DEMO_PREORDER)
        created.append("pre-order")
    if not ContactMessage.objects.filter(email=DEMO_MESSAGE_EMAIL).exists():
        ContactMessage.objects.create(**DEMO_MESSAGE)
        created.append("message")
    return created


def delete_demo_orders() -> int:
    """Delete only the demo orders, pre-order and message."""
    numbers = [fields["number"] for fields, _items in DEMO_ORDERS]
    deleted = Order.objects.filter(number__in=numbers).delete()[0]
    deleted += PreOrder.objects.filter(email=DEMO_PREORDER_EMAIL).delete()[0]
    deleted += ContactMessage.objects.filter(email=DEMO_MESSAGE_EMAIL).delete()[0]
    return deleted
