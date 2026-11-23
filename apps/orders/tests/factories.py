"""factory-boy factories of the orders app."""

from decimal import Decimal

import factory
from factory.django import DjangoModelFactory

from apps.orders.models import ContactMessage, Order, OrderItem, PreOrder


class OrderFactory(DjangoModelFactory):
    number = factory.Sequence(lambda n: f"261123-{1000 + n}")
    full_name = "Іван Тестовий"
    phone = "+380501234567"
    email = "ivan@example.com"
    total = Decimal("0")

    class Meta:
        model = Order


class OrderItemFactory(DjangoModelFactory):
    order = factory.SubFactory(OrderFactory)
    variety_name = "Рубін"
    kind = "cutting"
    quantity = 2
    unit_price = Decimal("30.00")

    class Meta:
        model = OrderItem


class PreOrderFactory(DjangoModelFactory):
    full_name = "Олена Тестова"
    phone = "+380671234567"
    description = "Рубін — 3 саджанці"

    class Meta:
        model = PreOrder


class ContactMessageFactory(DjangoModelFactory):
    name = "Петро"
    email = "petro@example.com"
    subject = "Питання"
    message = "Коли будуть саджанці?"

    class Meta:
        model = ContactMessage
