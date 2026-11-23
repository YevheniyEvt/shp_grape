"""
Email notifications about orders, pre-orders and contact messages.

The owner always gets Ukrainian emails (like the admin); the customer gets them in the language
the order was placed in. A failed email is logged and never breaks the request: the data is
already saved and visible in the admin.
"""

import logging
from collections.abc import Callable
from typing import Any

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext as _

from apps.content.models import SiteSettings
from apps.orders.models import ContactMessage, Order, PreOrder

logger = logging.getLogger(__name__)


def owner_email() -> str:
    """Where notifications for the owner go: the email from the site settings."""
    return SiteSettings.get_solo().email


def admin_url(obj: Order | PreOrder | ContactMessage) -> str:
    meta = obj._meta
    path = reverse(f"admin:{meta.app_label}_{meta.model_name}_change", args=[obj.pk])
    return f"{settings.BACKEND_URL.rstrip('/')}{path}"


def send(
    template: str,
    to: str,
    language: str,
    subject: Callable[[], str],
    context: dict[str, Any],
    reply_to: str = "",
) -> bool:
    """
    Render `<template>.txt` and `<template>.html` in `language` and send them to `to`.

    `subject` is called with the language active, so it may use gettext. Returns True on success.
    """
    try:
        with translation.override(language):
            context = {"site_name": SiteSettings.get_solo().site_name, **context}
            message = EmailMultiAlternatives(
                subject=subject(),
                body=render_to_string(f"{template}.txt", context),
                to=[to],
                reply_to=[reply_to] if reply_to else None,
            )
            message.attach_alternative(render_to_string(f"{template}.html", context), "text/html")
        message.send()
    except Exception:
        # The template name only: never log customer personal data.
        logger.exception("Failed to send the %s email", template)
        return False
    return True


def send_order_emails(order_id: int) -> None:
    """Notify the owner about a new order and send the customer a confirmation."""
    order = Order.objects.prefetch_related("items").get(pk=order_id)
    context = {"order": order, "items": list(order.items.all())}

    def subject() -> str:
        return _("Order %(number)s") % {"number": order.number}

    if recipient := owner_email():
        send(
            "orders/email/order_owner",
            recipient,
            settings.ADMIN_LANGUAGE_CODE,
            lambda: _("New order %(number)s") % {"number": order.number},
            context | {"admin_url": admin_url(order)},
            reply_to=order.email,
        )
    if order.email:
        send("orders/email/order_customer", order.email, order.language, subject, context)


def send_preorder_email(preorder_id: int) -> None:
    """Notify the owner about a new pre-order."""
    preorder = PreOrder.objects.get(pk=preorder_id)
    if recipient := owner_email():
        send(
            "orders/email/preorder_owner",
            recipient,
            settings.ADMIN_LANGUAGE_CODE,
            lambda: _("New pre-order from %(name)s") % {"name": preorder.full_name},
            {"preorder": preorder, "admin_url": admin_url(preorder)},
            reply_to=preorder.email,
        )


def send_contact_email(message_id: int) -> None:
    """Forward a contact form message to the owner; replying answers the visitor."""
    message = ContactMessage.objects.get(pk=message_id)
    if recipient := owner_email():
        send(
            "orders/email/contact_owner",
            recipient,
            settings.ADMIN_LANGUAGE_CODE,
            lambda: (
                _("Message from the website: %(subject)s")
                % {"subject": message.subject or message.name}
            ),
            {"message": message, "admin_url": admin_url(message)},
            reply_to=message.email,
        )
