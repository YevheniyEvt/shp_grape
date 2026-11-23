import pytest
from django.core import mail
from django.urls import reverse

from apps.catalog.tests.factories import VarietyPhotoFactory
from apps.orders.models import ContactMessage, Order, PreOrder

pytestmark = pytest.mark.django_db

CART_URL = reverse("orders:cart-validate")
ORDER_URL = reverse("orders:order-create")
PREORDER_URL = reverse("orders:preorder-create")
CONTACT_URL = reverse("orders:contact-create")


def order_payload(**overrides) -> dict:
    return {
        "full_name": "Іван Тестовий",
        "phone": "050 123 45 67",
        "email": "ivan@example.com",
        "city": "Київ",
        "delivery_office": "Відділення 5",
        "contact_method": "viber",
        "comment": "",
        "items": [
            {"variety": "rubin", "kind": "cutting", "quantity": 3, "price": "30.00"},
            {"variety": "rubin", "kind": "sapling", "quantity": 1, "price": 120},
        ],
        **overrides,
    }


def test_cart_validate(api_client, variety, sold_out):
    VarietyPhotoFactory(variety=variety, is_main=True)
    response = api_client.post(
        CART_URL,
        {
            "items": [
                {"variety": "rubin", "kind": "sapling", "quantity": 2, "price": 100},
                {"variety": "sapfir", "kind": "cutting", "quantity": 1},
                {"variety": "missing", "kind": "cutting", "quantity": 1},
            ]
        },
        format="json",
        HTTP_ACCEPT_LANGUAGE="en",
    )
    assert response.status_code == 200
    data = response.json()
    first, second, third = data["items"]
    assert first["name"] == "Ruby"
    assert first["price"] == 120
    assert first["problem"] == "price_changed"
    assert first["photo"]["thumb"].startswith("http://testserver/")
    assert second == {
        "variety": "sapfir",
        "kind": "cutting",
        "quantity": 1,
        "name": "Sapphire",
        "price": 40,
        "available": False,
        "problem": "unavailable",
        "photo": None,
    }
    assert third["name"] is None
    assert third["problem"] == "not_found"
    # Unavailable items are not counted.
    assert data["total"] == 240
    assert data["has_problems"] is True


@pytest.mark.parametrize(
    "items",
    [
        [],
        [{"variety": "rubin", "kind": "seed", "quantity": 1}],
        [{"variety": "rubin", "kind": "cutting", "quantity": 0}],
        [{"variety": "rubin", "kind": "cutting", "quantity": 100}],
        [{"variety": "rubin", "kind": "cutting", "quantity": 1}] * 51,
    ],
)
def test_cart_validate_rejects_bad_items(api_client, items):
    response = api_client.post(CART_URL, {"items": items}, format="json")
    assert response.status_code == 400


def test_create_order(api_client, variety, owner_email, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        response = api_client.post(
            ORDER_URL, order_payload(), format="json", HTTP_ACCEPT_LANGUAGE="en"
        )
    assert response.status_code == 201, response.json()
    order = Order.objects.get()
    assert response.json() == {"number": order.number, "total": 210}
    assert order.phone == "+380501234567"
    assert order.language == "en"
    assert order.contact_method == "viber"
    assert order.items.count() == 2
    assert [m.to for m in mail.outbox] == [[owner_email], ["ivan@example.com"]]
    assert all("Ruby" in m.body for m in mail.outbox)


def test_order_without_price_uses_current_one(api_client, variety):
    payload = order_payload(items=[{"variety": "rubin", "kind": "cutting", "quantity": 2}])
    response = api_client.post(ORDER_URL, payload, format="json")
    assert response.status_code == 201
    assert response.json()["total"] == 60


def test_forged_order_of_unavailable_variety_is_rejected(api_client, variety, sold_out):
    payload = order_payload(
        items=[
            {"variety": "rubin", "kind": "cutting", "quantity": 1, "price": 30},
            {"variety": "sapfir", "kind": "cutting", "quantity": 1, "price": 40},
        ]
    )
    response = api_client.post(ORDER_URL, payload, format="json")
    assert response.status_code == 409
    data = response.json()
    assert data["detail"]
    assert [item["problem"] for item in data["items"]] == [None, "unavailable"]
    assert not Order.objects.exists()


def test_order_with_changed_price_is_rejected(api_client, variety):
    payload = order_payload(
        items=[{"variety": "rubin", "kind": "cutting", "quantity": 1, "price": "1.00"}]
    )
    response = api_client.post(ORDER_URL, payload, format="json")
    assert response.status_code == 409
    assert response.json()["items"][0]["price"] == 30
    assert not Order.objects.exists()


@pytest.mark.parametrize(
    ("override", "field"),
    [
        ({"full_name": ""}, "full_name"),
        ({"phone": "12345"}, "phone"),
        ({"email": "not-an-email"}, "email"),
        ({"contact_method": "pigeon"}, "contact_method"),
        ({"items": []}, "items"),
        ({"website": "http://spam.example"}, "website"),
    ],
)
def test_order_validation(api_client, variety, override, field):
    response = api_client.post(ORDER_URL, order_payload(**override), format="json")
    assert response.status_code == 400
    assert field in response.json()
    assert not Order.objects.exists()


def test_validation_errors_follow_language(api_client, variety):
    response = api_client.post(
        ORDER_URL, order_payload(phone="1"), format="json", HTTP_ACCEPT_LANGUAGE="uk"
    )
    message = response.json()["phone"][0]
    assert "+380" in message
    assert "Введіть" in message


def test_order_throttling(api_client, variety, settings):
    limit = int(settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["orders"].split("/")[0])
    payload = order_payload(items=[{"variety": "rubin", "kind": "cutting", "quantity": 1}])
    statuses = [
        api_client.post(ORDER_URL, payload, format="json").status_code for _ in range(limit + 1)
    ]
    assert statuses[:limit] == [201] * limit
    assert statuses[-1] == 429
    assert Order.objects.count() == limit


def test_create_preorder(api_client, owner_email, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        response = api_client.post(
            PREORDER_URL,
            {
                "full_name": "Оля",
                "phone": "+380 67 123 45 67",
                "description": "Рубін — 5 саджанців навесні",
            },
            format="json",
        )
    assert response.status_code == 201
    assert PreOrder.objects.get().phone == "+380671234567"
    assert len(mail.outbox) == 1


def test_preorder_honeypot(api_client):
    response = api_client.post(
        PREORDER_URL,
        {"full_name": "Bot", "phone": "0501234567", "description": "x", "website": "spam"},
        format="json",
    )
    assert response.status_code == 400
    assert not PreOrder.objects.exists()


def test_create_contact_message(api_client, owner_email, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        response = api_client.post(
            CONTACT_URL,
            {"name": "Петро", "email": "petro@example.com", "message": "Привіт!", "website": ""},
            format="json",
            HTTP_ACCEPT_LANGUAGE="en",
        )
    assert response.status_code == 201
    message = ContactMessage.objects.get()
    assert message.language == "en"
    assert message.subject == ""
    assert mail.outbox[0].reply_to == ["petro@example.com"]


def test_contact_message_validation(api_client):
    response = api_client.post(CONTACT_URL, {"name": "", "email": "x"}, format="json")
    assert response.status_code == 400
    assert set(response.json()) == {"name", "email", "message"}


def test_forms_throttling(api_client, settings):
    limit = int(settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["forms"].split("/")[0])
    payload = {"name": "Петро", "email": "petro@example.com", "message": "Привіт"}
    statuses = [
        api_client.post(CONTACT_URL, payload, format="json").status_code for _ in range(limit + 1)
    ]
    assert statuses[-1] == 429
    assert ContactMessage.objects.count() == limit


def test_unknown_language_falls_back_to_default(api_client, variety):
    payload = order_payload(items=[{"variety": "rubin", "kind": "cutting", "quantity": 1}])
    api_client.post(ORDER_URL, payload, format="json", HTTP_ACCEPT_LANGUAGE="de")
    assert Order.objects.get().language == "uk"
