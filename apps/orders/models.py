"""Models of the orders app: orders with their items, pre-orders and contact messages."""

from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel

# The largest quantity of one item in an order (the frontend uses the same limit).
MAX_ITEM_QUANTITY = 99


class ProductKind(models.TextChoices):
    """What is sold for a variety."""

    CUTTING = "cutting", _("cutting")
    SAPLING = "sapling", _("sapling")


class ContactMethod(models.TextChoices):
    """How the customer prefers to be contacted."""

    PHONE = "phone", _("phone call")
    VIBER = "viber", _("Viber")
    TELEGRAM = "telegram", _("Telegram")
    EMAIL = "email", _("email")


class CustomerContactsMixin(models.Model):
    """Name and contacts shared by orders and pre-orders."""

    full_name = models.CharField(_("full name"), max_length=200)
    phone = models.CharField(_("phone"), max_length=20, db_index=True)
    email = models.EmailField(_("email"), blank=True)
    language = models.CharField(
        _("language"),
        max_length=8,
        choices=settings.LANGUAGES,
        default=settings.LANGUAGE_CODE,
        help_text=_(
            "Language of the site when the request was sent; the customer's emails use it."
        ),
    )

    class Meta:
        abstract = True


class Order(CustomerContactsMixin, TimeStampedModel):
    """A customer's order of cuttings and saplings."""

    class Status(models.TextChoices):
        NEW = "new", _("new")
        CONFIRMED = "confirmed", _("confirmed")
        SHIPPED = "shipped", _("shipped")
        DONE = "done", _("done")
        CANCELLED = "cancelled", _("cancelled")

    number = models.CharField(_("number"), max_length=20, unique=True, editable=False)
    city = models.CharField(_("city"), max_length=100, blank=True)
    delivery_office = models.CharField(
        _("Nova Poshta office"),
        max_length=200,
        blank=True,
        help_text=_("Branch or parcel locker number, as the customer wrote it."),
    )
    contact_method = models.CharField(
        _("preferred contact"),
        max_length=16,
        choices=ContactMethod.choices,
        default=ContactMethod.PHONE,
    )
    comment = models.TextField(_("customer comment"), blank=True)
    status = models.CharField(
        _("status"), max_length=16, choices=Status.choices, default=Status.NEW, db_index=True
    )
    total = models.DecimalField(
        _("total, UAH"), max_digits=12, decimal_places=2, default=Decimal(0), editable=False
    )
    admin_note = models.TextField(
        _("admin note"), blank=True, help_text=_("Visible only in the admin.")
    )

    class Meta:
        verbose_name = _("order")
        verbose_name_plural = _("orders")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return _("Order %(number)s") % {"number": self.number}


class OrderItem(models.Model):
    """
    A line of an order.

    The variety name and the unit price are copied when the order is placed, so later changes in
    the catalog (or a deleted variety) never change an existing order.
    """

    order = models.ForeignKey(
        Order, verbose_name=_("order"), on_delete=models.CASCADE, related_name="items"
    )
    variety = models.ForeignKey(
        "catalog.Variety",
        verbose_name=_("variety"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
    )
    variety_name = models.CharField(_("variety name"), max_length=200)
    kind = models.CharField(_("type"), max_length=16, choices=ProductKind.choices)
    quantity = models.PositiveIntegerField(
        _("quantity"), validators=[MinValueValidator(1), MaxValueValidator(MAX_ITEM_QUANTITY)]
    )
    unit_price = models.DecimalField(_("unit price, UAH"), max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = _("order item")
        verbose_name_plural = _("order items")
        ordering = ["pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["order", "variety", "kind"], name="orders_item_unique_product"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.variety_name} ({self.get_kind_display()}) × {self.quantity}"

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity


class PreOrder(CustomerContactsMixin, TimeStampedModel):
    """A request for varieties that are not available yet (next season)."""

    class Status(models.TextChoices):
        NEW = "new", _("new")
        IN_PROGRESS = "in_progress", _("in progress")
        DONE = "done", _("done")
        CANCELLED = "cancelled", _("cancelled")

    description = models.TextField(
        _("what is wanted"), help_text=_("Varieties, types and quantities in free form.")
    )
    status = models.CharField(
        _("status"), max_length=16, choices=Status.choices, default=Status.NEW, db_index=True
    )
    admin_note = models.TextField(
        _("admin note"), blank=True, help_text=_("Visible only in the admin.")
    )

    class Meta:
        verbose_name = _("pre-order")
        verbose_name_plural = _("pre-orders")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return _("Pre-order from %(name)s") % {"name": self.full_name}


class ContactMessage(TimeStampedModel):
    """A message sent with the form on the contacts page."""

    name = models.CharField(_("name"), max_length=200)
    email = models.EmailField(_("email"))
    subject = models.CharField(_("subject"), max_length=200, blank=True)
    message = models.TextField(_("message"))
    language = models.CharField(
        _("language"), max_length=8, choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE
    )
    is_processed = models.BooleanField(_("processed"), default=False, db_index=True)

    class Meta:
        verbose_name = _("contact message")
        verbose_name_plural = _("contact messages")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.subject or self.message[:50]
