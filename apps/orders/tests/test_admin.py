import pytest
from django.urls import reverse

from apps.orders.models import ContactMessage, Order, PreOrder
from apps.orders.tests.factories import (
    ContactMessageFactory,
    OrderFactory,
    OrderItemFactory,
    PreOrderFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client(client, django_user_model):
    user = django_user_model.objects.create_superuser("admin", "admin@example.com", "password")
    client.force_login(user)
    return client


@pytest.mark.parametrize(
    ("model", "factory"),
    [
        ("order", OrderFactory),
        ("preorder", PreOrderFactory),
        ("contactmessage", ContactMessageFactory),
    ],
)
def test_admin_pages_open(admin_client, model, factory):
    obj = factory()
    if model == "order":
        OrderItemFactory(order=obj)
    changelist = reverse(f"admin:orders_{model}_changelist")
    assert admin_client.get(changelist).status_code == 200
    assert admin_client.get(changelist, {"q": "050"}).status_code == 200
    change = reverse(f"admin:orders_{model}_change", args=[obj.pk])
    assert admin_client.get(change).status_code == 200
    # Requests come only from the website.
    assert admin_client.get(reverse(f"admin:orders_{model}_add")).status_code == 403


def test_order_changelist_shows_items_count(admin_client):
    order = OrderFactory()
    OrderItemFactory(order=order)
    OrderItemFactory(order=order, kind="sapling")
    response = admin_client.get(reverse("admin:orders_order_changelist"))
    assert response.context["cl"].result_list[0].items_total == 2


@pytest.mark.parametrize(
    ("query", "found"),
    [("050 123", True), ("+38 (050) 123-45-67", True), ("0671", False), ("Іван", True)],
)
def test_order_search_by_phone(admin_client, query, found):
    OrderFactory(phone="+380501234567", full_name="Іван Тестовий")
    response = admin_client.get(reverse("admin:orders_order_changelist"), {"q": query})
    assert (len(response.context["cl"].result_list) == 1) is found


def test_order_status_action(admin_client):
    orders = [OrderFactory(), OrderFactory()]
    response = admin_client.post(
        reverse("admin:orders_order_changelist"),
        {"action": "mark_shipped", "_selected_action": [o.pk for o in orders]},
        follow=True,
    )
    assert response.status_code == 200
    assert set(Order.objects.values_list("status", flat=True)) == {Order.Status.SHIPPED}
    assert "позначено" in response.content.decode()


def test_preorder_status_action(admin_client):
    preorder = PreOrderFactory()
    admin_client.post(
        reverse("admin:orders_preorder_changelist"),
        {"action": "mark_in_progress", "_selected_action": [preorder.pk]},
    )
    preorder.refresh_from_db()
    assert preorder.status == PreOrder.Status.IN_PROGRESS


def test_contact_message_processed_action(admin_client):
    message = ContactMessageFactory()
    admin_client.post(
        reverse("admin:orders_contactmessage_changelist"),
        {"action": "mark_processed", "_selected_action": [message.pk]},
    )
    assert ContactMessage.objects.get().is_processed


def test_preorder_short_description():
    from django.contrib.admin.sites import site

    model_admin = site._registry[PreOrder]
    assert model_admin.short_description(PreOrderFactory(description="a" * 100)).endswith("…")
    assert model_admin.short_description(PreOrderFactory(description="short")) == "short"


def test_str_methods():
    order = OrderFactory(number="261123-1000")
    assert str(order) == "Замовлення 261123-1000"
    assert str(OrderItemFactory(order=order, variety_name="Рубін", quantity=2)) == (
        "Рубін (живець) × 2"
    )
    assert str(PreOrderFactory(full_name="Оля")) == "Передзамовлення від Оля"
    assert str(ContactMessageFactory(subject="Питання")) == "Питання"
    assert str(ContactMessageFactory(subject="", message="Текст")) == "Текст"
