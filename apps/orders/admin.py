"""Admin of the orders app: orders, pre-orders and contact messages."""

import re

from django.contrib import admin, messages
from django.db.models import Count, QuerySet
from django.http import HttpRequest
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from apps.orders import services
from apps.orders.models import ContactMessage, Order, OrderItem, PreOrder

ADMIN_CSS = {"all": ["core/admin.css"]}


class PhoneSearchMixin:
    """
    Find by phone however it is typed: `050 123`, `+38(050)123-45`.

    Phones are stored as `+380501234567`, so the digits of the query are also searched.
    """

    def get_search_results(self, request: HttpRequest, queryset: QuerySet, search_term: str):
        results, may_have_duplicates = super().get_search_results(request, queryset, search_term)
        digits = re.sub(r"\D", "", search_term)
        if len(digits) >= 3:
            # A local number starts with 0, the stored one with 380: drop the leading 0.
            results |= queryset.filter(phone__contains=digits.removeprefix("0") or digits)
        return results, may_have_duplicates


def status_actions(model: type[Order] | type[PreOrder]) -> list:
    """One admin action per status: «Mark as <status>»."""

    def make(value: str, label: str):
        def action(modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet):
            changed = services.set_status(queryset, value)
            modeladmin.message_user(
                request,
                ngettext(
                    "%(count)d entry marked as «%(status)s».",
                    "%(count)d entries marked as «%(status)s».",
                    changed,
                )
                % {"count": changed, "status": label},
                messages.SUCCESS,
            )

        action.__name__ = f"mark_{value}"
        return admin.action(description=format_lazy(_("Mark as «{status}»"), status=label))(action)

    return [make(value, label) for value, label in model.Status.choices]


class OrderItemInline(admin.TabularInline):
    """Items are a snapshot of the order and are not edited."""

    model = OrderItem
    extra = 0
    can_delete = False
    fields = ["variety_name", "variety", "kind", "quantity", "unit_price", "line_total"]
    readonly_fields = fields

    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    @admin.display(description=_("sum, UAH"))
    def line_total(self, item: OrderItem):
        return item.line_total


@admin.register(Order)
class OrderAdmin(PhoneSearchMixin, admin.ModelAdmin):
    list_display = [
        "number",
        "created_at",
        "full_name",
        "phone",
        "items_count",
        "total",
        "status",
    ]
    list_display_links = ["number", "full_name"]
    list_filter = ["status", "created_at", "contact_method", "language"]
    search_fields = ["number", "full_name", "email", "city"]
    date_hierarchy = "created_at"
    readonly_fields = ["number", "total", "language", "created_at", "updated_at"]
    fieldsets = [
        (None, {"fields": ["number", "status", "total", "admin_note"]}),
        (
            _("Customer"),
            {"fields": ["full_name", "phone", "email", "contact_method", "language"]},
        ),
        (_("Delivery"), {"fields": ["city", "delivery_office", "comment"]}),
        (_("Dates"), {"fields": ["created_at", "updated_at"]}),
    ]
    inlines = [OrderItemInline]
    actions = status_actions(Order)

    class Media:
        css = ADMIN_CSS

    def get_queryset(self, request: HttpRequest) -> QuerySet[Order]:
        return super().get_queryset(request).annotate(items_total=Count("items"))

    def has_add_permission(self, request: HttpRequest) -> bool:
        # Orders come from the website: the number, items and total are computed there.
        return False

    @admin.display(description=_("items"), ordering="items_total")
    def items_count(self, order: Order) -> int:
        return order.items_total


@admin.register(PreOrder)
class PreOrderAdmin(PhoneSearchMixin, admin.ModelAdmin):
    list_display = ["created_at", "full_name", "phone", "short_description", "status"]
    list_display_links = ["created_at", "full_name"]
    list_filter = ["status", "created_at", "language"]
    search_fields = ["full_name", "email", "description"]
    date_hierarchy = "created_at"
    readonly_fields = ["language", "created_at", "updated_at"]
    fields = [
        "status",
        "full_name",
        "phone",
        "email",
        "description",
        "admin_note",
        "language",
        "created_at",
        "updated_at",
    ]
    actions = status_actions(PreOrder)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    @admin.display(description=_("what is wanted"))
    def short_description(self, preorder: PreOrder) -> str:
        text = preorder.description
        return text if len(text) <= 80 else f"{text[:80]}…"


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ["created_at", "name", "email", "subject", "is_processed"]
    list_display_links = ["created_at", "name"]
    list_editable = ["is_processed"]
    list_filter = ["is_processed", "created_at", "language"]
    search_fields = ["name", "email", "subject", "message"]
    date_hierarchy = "created_at"
    readonly_fields = ["name", "email", "subject", "message", "language", "created_at"]
    fields = ["is_processed", "name", "email", "subject", "message", "language", "created_at"]
    actions = ["mark_processed"]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    @admin.action(description=_("Mark as processed"))
    def mark_processed(self, request: HttpRequest, queryset: QuerySet[ContactMessage]) -> None:
        changed = queryset.filter(is_processed=False).update(is_processed=True)
        self.message_user(
            request,
            ngettext("%(count)d message processed.", "%(count)d messages processed.", changed)
            % {"count": changed},
            messages.SUCCESS,
        )
