from django.urls import path

from apps.orders import views

app_name = "orders"

urlpatterns = [
    path("cart/validate/", views.CartValidateView.as_view(), name="cart-validate"),
    path("orders/", views.OrderCreateView.as_view(), name="order-create"),
    path("preorders/", views.PreOrderCreateView.as_view(), name="preorder-create"),
    path("contact/", views.ContactMessageCreateView.as_view(), name="contact-create"),
]
