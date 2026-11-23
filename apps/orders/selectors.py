"""Read-only queries of the orders app: checking cart items against the catalog."""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from django.db.models import QuerySet

from apps.catalog.models import Variety
from apps.catalog.selectors import card_photos_prefetch, published_varieties
from apps.orders.models import MAX_ITEM_QUANTITY, ProductKind


class Problem(StrEnum):
    """Why a cart item cannot be ordered as it is."""

    NOT_FOUND = "not_found"
    UNAVAILABLE = "unavailable"
    PRICE_CHANGED = "price_changed"


@dataclass(frozen=True)
class CartItem:
    """An item as the client sends it: what, how many and (optionally) the price it showed."""

    slug: str
    kind: str
    quantity: int
    price: Decimal | None = None


@dataclass(frozen=True)
class CartLine:
    """A cart item checked against the current catalog."""

    item: CartItem
    variety: Variety | None
    price: Decimal | None
    available: bool
    problem: Problem | None

    @property
    def line_total(self) -> Decimal:
        return (self.price or Decimal(0)) * self.item.quantity


def merge_items(items: Iterable[CartItem]) -> list[CartItem]:
    """Join repeated (variety, kind) items, keeping the first price and capping the quantity."""
    merged: dict[tuple[str, str], CartItem] = {}
    for item in items:
        key = (item.slug, item.kind)
        if key in merged:
            first = merged[key]
            quantity = min(first.quantity + item.quantity, MAX_ITEM_QUANTITY)
            merged[key] = CartItem(item.slug, item.kind, quantity, first.price)
        else:
            merged[key] = item
    return list(merged.values())


def offer(variety: Variety, kind: str) -> tuple[Decimal | None, bool]:
    """The current price of `kind` for `variety` and whether it can be ordered."""
    if kind == ProductKind.CUTTING:
        price, in_stock = variety.cutting_price, variety.cutting_available
    else:
        price, in_stock = variety.sapling_price, variety.sapling_available
    return price, in_stock and price is not None


def check_items(items: Iterable[CartItem], varieties: QuerySet[Variety]) -> list[CartLine]:
    """
    Check every item against `varieties` (published ones, by slug).

    A price sent by the client that differs from the current one is a `price_changed` problem,
    so the customer always confirms the price they pay.
    """
    items = merge_items(items)
    by_slug = {
        variety.slug: variety for variety in varieties.filter(slug__in={i.slug for i in items})
    }
    lines = []
    for item in items:
        variety = by_slug.get(item.slug)
        if variety is None:
            lines.append(CartLine(item, None, None, False, Problem.NOT_FOUND))
            continue
        price, available = offer(variety, item.kind)
        if not available:
            problem: Problem | None = Problem.UNAVAILABLE
        elif item.price is not None and item.price != price:
            problem = Problem.PRICE_CHANGED
        else:
            problem = None
        lines.append(CartLine(item, variety, price, available, problem))
    return lines


def cart_lines(items: Iterable[CartItem]) -> list[CartLine]:
    """Check cart items for the cart page: current names, prices, availability and photos."""
    return check_items(items, published_varieties().prefetch_related(card_photos_prefetch()))
