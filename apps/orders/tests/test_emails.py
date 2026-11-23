from unittest import mock

import pytest
from django.core import mail

from apps.orders import emails
from apps.orders.tests.factories import (
    ContactMessageFactory,
    OrderFactory,
    OrderItemFactory,
    PreOrderFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def order():
    order = OrderFactory(
        number="261123-4821",
        language="en",
        total="180.00",
        full_name="John & Co",
        city="Kyiv",
        delivery_office="Branch 5",
        comment="Call after 18:00",
    )
    OrderItemFactory(order=order, variety_name="Ruby", quantity=2, unit_price="30.00")
    OrderItemFactory(
        order=order, variety_name="Ruby", kind="sapling", quantity=1, unit_price="120.00"
    )
    return order


def test_order_emails_owner_in_ukrainian_customer_in_order_language(owner_email, order):
    emails.send_order_emails(order.pk)

    owner, customer = mail.outbox
    assert owner.to == [owner_email]
    assert owner.subject == "Нове замовлення 261123-4821"
    assert owner.reply_to == ["ivan@example.com"]
    assert "Ruby, живець: 2 × 30 ₴ = 60 ₴" in owner.body
    assert f"/orders/order/{order.pk}/change/" in owner.body
    assert "180 ₴" in owner.body
    # Plain text is not HTML-escaped; the HTML part is.
    assert "John & Co" in owner.body
    html = owner.alternatives[0].content
    assert "John &amp; Co" in html
    assert "Branch 5" in html

    assert customer.to == ["ivan@example.com"]
    assert customer.subject == "Order 261123-4821"
    assert "Thank you for your order 261123-4821" in customer.body
    assert "Ruby, cutting: 2 × 30 ₴ = 60 ₴" in customer.body
    assert "/change/" not in customer.body


def test_order_without_customer_email_or_owner_email(order):
    order.email = ""
    order.save()
    emails.send_order_emails(order.pk)
    assert mail.outbox == []


def test_preorder_email(owner_email):
    preorder = PreOrderFactory(email="olena@example.com")
    emails.send_preorder_email(preorder.pk)
    [message] = mail.outbox
    assert message.to == [owner_email]
    assert message.subject == "Нове передзамовлення від Олена Тестова"
    assert "Рубін — 3 саджанці" in message.body
    assert message.reply_to == ["olena@example.com"]


def test_contact_email(owner_email):
    contact = ContactMessageFactory()
    emails.send_contact_email(contact.pk)
    [message] = mail.outbox
    assert message.subject == "Повідомлення з сайту: Питання"
    assert message.reply_to == ["petro@example.com"]
    assert "Коли будуть саджанці?" in message.body


def test_contact_email_without_subject(owner_email):
    contact = ContactMessageFactory(subject="")
    emails.send_contact_email(contact.pk)
    assert mail.outbox[0].subject == "Повідомлення з сайту: Петро"


def test_no_owner_email_no_messages():
    emails.send_preorder_email(PreOrderFactory().pk)
    emails.send_contact_email(ContactMessageFactory().pk)
    assert mail.outbox == []


def test_failed_email_is_logged_not_raised(owner_email, caplog):
    contact = ContactMessageFactory()
    with mock.patch.object(emails.EmailMultiAlternatives, "send", side_effect=OSError("smtp")):
        assert not emails.send(
            "orders/email/contact_owner",
            owner_email,
            "uk",
            lambda: "subject",
            {"message": contact, "admin_url": ""},
        )
    assert "Failed to send the orders/email/contact_owner email" in caplog.text
    # No personal data in the log.
    assert "petro@example.com" not in caplog.text
