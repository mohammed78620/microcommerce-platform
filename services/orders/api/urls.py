from django.urls import path
from .views.views import OrderViewSet, CartViewSet
from .views.stripe_webhook_view import StripeWebhookView

urlpatterns = [
    path("webhook/", StripeWebhookView.as_view(), name="stripe-webhook"),
    path("orders/", OrderViewSet.as_view({"post": "create"})),
    path("orders/<int:user_id>", OrderViewSet.as_view({"get": "list"})),
    path("cart/", CartViewSet.as_view({"get": "list"})),
    path("cart/checkout/", CartViewSet.as_view({"post": "checkout"})),
    path("cart/<int:product_id>/", CartViewSet.as_view({"post": "add", "delete": "remove"})),
]
