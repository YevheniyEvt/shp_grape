"""Public API of the orders app: cart check, checkout, pre-order and contact forms."""

from decimal import Decimal

from django.conf import settings
from django.utils import translation
from django.utils.translation import gettext as _
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.catalog.views import PublicAPIMixin
from apps.orders import selectors, services
from apps.orders.serializers import (
    CartLineSerializer,
    CartValidateRequestSerializer,
    CartValidateResponseSerializer,
    ContactMessageCreateSerializer,
    OrderCreatedSerializer,
    OrderCreateSerializer,
    OrderRejectedSerializer,
    PreOrderCreateSerializer,
)


def request_language() -> str:
    """The site language of the current request (`Accept-Language`, set by LocaleMiddleware)."""
    language = translation.get_language()
    codes = {code for code, _name in settings.LANGUAGES}
    return language if language in codes else settings.LANGUAGE_CODE


class ThrottledFormMixin(PublicAPIMixin):
    """Anonymous POST endpoints limited per IP address (rates in `DEFAULT_THROTTLE_RATES`)."""

    throttle_classes = [ScopedRateThrottle]


class CartValidateView(ThrottledFormMixin, APIView):
    """Current names, prices, availability and photos of cart items."""

    throttle_scope = "cart"

    @extend_schema(request=CartValidateRequestSerializer, responses=CartValidateResponseSerializer)
    def post(self, request: Request) -> Response:
        serializer = CartValidateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lines = selectors.cart_lines(serializer.validated_data["items"])
        data = {
            "items": lines,
            "total": sum((line.line_total for line in lines if line.available), Decimal(0)),
            "has_problems": any(line.problem for line in lines),
        }
        return Response(CartValidateResponseSerializer(data, context={"request": request}).data)


class OrderCreateView(ThrottledFormMixin, APIView):
    """
    Place an order. Prices and availability are checked on the server.

    Returns 409 with the checked items when any of them is unknown, out of stock or has a
    different price than the client sent.
    """

    throttle_scope = "orders"

    @extend_schema(
        request=OrderCreateSerializer,
        responses={201: OrderCreatedSerializer, 409: OrderRejectedSerializer},
    )
    def post(self, request: Request) -> Response:
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = dict(serializer.validated_data)
        items = customer.pop("items")
        try:
            order = services.place_order(customer, items, request_language())
        except services.OrderRejected as rejected:
            data = {
                "detail": _("Some items in your cart have changed. Please check the cart."),
                "items": CartLineSerializer(
                    rejected.lines, many=True, context={"request": request}
                ).data,
            }
            return Response(data, status=status.HTTP_409_CONFLICT)
        return Response(OrderCreatedSerializer(order).data, status=status.HTTP_201_CREATED)


class PreOrderCreateView(ThrottledFormMixin, APIView):
    """Send a pre-order (free-form request for the next season)."""

    throttle_scope = "forms"

    @extend_schema(request=PreOrderCreateSerializer, responses={201: None})
    def post(self, request: Request) -> Response:
        serializer = PreOrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.create_preorder(serializer.validated_data, request_language())
        return Response(status=status.HTTP_201_CREATED)


class ContactMessageCreateView(ThrottledFormMixin, APIView):
    """Send a message to the owner from the contacts page."""

    throttle_scope = "forms"

    @extend_schema(request=ContactMessageCreateSerializer, responses={201: None})
    def post(self, request: Request) -> Response:
        serializer = ContactMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.create_contact_message(serializer.validated_data, request_language())
        return Response(status=status.HTTP_201_CREATED)
