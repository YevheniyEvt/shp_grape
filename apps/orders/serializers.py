"""Serializers of the orders API: the cart check, the checkout, pre-order and contact forms."""

from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.catalog.serializers import PhotoSerializer
from apps.orders.models import MAX_ITEM_QUANTITY, ContactMessage, Order, PreOrder, ProductKind
from apps.orders.phones import normalize_phone
from apps.orders.selectors import CartItem, CartLine, Problem

MAX_CART_ITEMS = 50


class HoneypotMixin(serializers.Serializer):
    """
    A field hidden from people with CSS: bots fill every input, so a value means spam.

    The frontend renders it as `website`, off-screen and without tab focus.
    """

    website = serializers.CharField(
        required=False, allow_blank=True, write_only=True, max_length=200
    )

    def validate_website(self, value: str) -> str:
        if value:
            raise serializers.ValidationError("Spam detected.")
        return value

    def validate(self, attrs: dict) -> dict:
        attrs.pop("website", None)
        return super().validate(attrs)


class PhoneField(serializers.CharField):
    default_error_messages = {
        "invalid_phone": _("Enter a valid phone number, e.g. +380 50 123 45 67."),
    }

    def to_internal_value(self, data) -> str:
        phone = normalize_phone(super().to_internal_value(data))
        if phone is None:
            self.fail("invalid_phone")
        return phone


class CartItemSerializer(serializers.Serializer):
    variety = serializers.SlugField(help_text="Variety slug.")
    kind = serializers.ChoiceField(choices=ProductKind.choices)
    quantity = serializers.IntegerField(min_value=1, max_value=MAX_ITEM_QUANTITY)
    price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True,
        help_text="Unit price the customer saw; a different current price is reported.",
    )


class CartItemsField(serializers.ListField):
    child = CartItemSerializer()

    def __init__(self, **kwargs) -> None:
        super().__init__(min_length=1, max_length=MAX_CART_ITEMS, **kwargs)

    def to_internal_value(self, data) -> list[CartItem]:
        return [
            CartItem(item["variety"], item["kind"], item["quantity"], item.get("price"))
            for item in super().to_internal_value(data)
        ]


class CartValidateRequestSerializer(serializers.Serializer):
    items = CartItemsField()


class CartLineSerializer(serializers.Serializer):
    """A cart item with the current data of its variety."""

    variety = serializers.CharField(source="item.slug")
    kind = serializers.CharField(source="item.kind")
    quantity = serializers.IntegerField(source="item.quantity")
    name = serializers.SerializerMethodField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    available = serializers.BooleanField()
    problem = serializers.ChoiceField(choices=[p.value for p in Problem], allow_null=True)
    photo = serializers.SerializerMethodField()

    def get_name(self, line: CartLine) -> str | None:
        return line.variety.name if line.variety else None

    @extend_schema_field(PhotoSerializer(allow_null=True))
    def get_photo(self, line: CartLine) -> dict | None:
        photos = getattr(line.variety, "card_photos", None)
        return PhotoSerializer(photos[0], context=self.context).data if photos else None


class CartValidateResponseSerializer(serializers.Serializer):
    items = CartLineSerializer(many=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2)
    has_problems = serializers.BooleanField()


class OrderCreateSerializer(HoneypotMixin, serializers.ModelSerializer):
    phone = PhoneField(max_length=30)
    items = CartItemsField()

    class Meta:
        model = Order
        fields = [
            "full_name",
            "phone",
            "email",
            "city",
            "delivery_office",
            "contact_method",
            "comment",
            "items",
            "website",
        ]
        extra_kwargs = {"comment": {"max_length": 2000}}


class OrderCreatedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["number", "total"]


class OrderRejectedSerializer(serializers.Serializer):
    """Returned with HTTP 409 when items changed: the cart shows the new data."""

    detail = serializers.CharField()
    items = CartLineSerializer(many=True)


class PreOrderCreateSerializer(HoneypotMixin, serializers.ModelSerializer):
    phone = PhoneField(max_length=30)

    class Meta:
        model = PreOrder
        fields = ["full_name", "phone", "email", "description", "website"]
        extra_kwargs = {"description": {"max_length": 2000}}


class ContactMessageCreateSerializer(HoneypotMixin, serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message", "website"]
        extra_kwargs = {"message": {"max_length": 5000}}
