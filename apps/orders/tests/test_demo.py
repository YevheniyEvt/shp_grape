from decimal import Decimal

import pytest
from django.core import mail

from apps.catalog import demo as catalog_demo
from apps.catalog.tests.factories import VarietyFactory
from apps.orders import demo
from apps.orders.models import ContactMessage, Order, PreOrder
from apps.orders.tests.factories import ContactMessageFactory, OrderFactory, PreOrderFactory

pytestmark = pytest.mark.django_db


def test_frozen_items_match_demo_varieties():
    names = {item.slug: item.fields for item in catalog_demo.DEMO_VARIETIES}
    for fields, items in demo.DEMO_ORDERS:
        for item in items:
            assert item.name == names[item.slug][f"name_{fields['language']}"]
            price = names[item.slug][f"{item.kind}_price"]
            assert item.price == price


def test_seed_orders_is_idempotent_and_links_varieties():
    variety = VarietyFactory(slug="rankovyi-ametyst")

    created = demo.seed_orders()

    assert created == ["DEMO-0001", "DEMO-0002", "pre-order", "message"]
    assert demo.seed_orders() == []
    first = Order.objects.get(number="DEMO-0001")
    assert first.total == Decimal("450")
    assert first.items.filter(variety=variety).count() == 2
    # Varieties that do not exist stay unlinked: the snapshot keeps the name.
    assert first.items.get(variety__isnull=True).variety_name == "Білий Туман"
    assert set(Order.objects.values_list("status", flat=True)) == {"new", "shipped"}
    assert PreOrder.objects.count() == 1
    assert ContactMessage.objects.count() == 1
    assert mail.outbox == []


def test_delete_demo_orders_keeps_real_requests():
    real = [OrderFactory(), PreOrderFactory(), ContactMessageFactory()]
    demo.seed_orders()

    assert demo.delete_demo_orders() == 2 + 4 + 1 + 1  # orders, their items, pre-order, message

    assert list(Order.objects.all()) == [real[0]]
    assert list(PreOrder.objects.all()) == [real[1]]
    assert list(ContactMessage.objects.all()) == [real[2]]
