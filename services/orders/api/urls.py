from django.urls import path
<<<<<<< HEAD
from .views.views import OrderViewSet, CartViewSet
from .views.stripe_webhook_view import StripeWebhookView
=======
from .views import OrderViewSet
>>>>>>> main

urlpatterns = [
    path("webhook/", StripeWebhookView.as_view(), name="stripe-webhook"),
    path("orders/", OrderViewSet.as_view({"get": "list", "post": "create"})),
<<<<<<< HEAD
    path("cart/", CartViewSet.as_view({"get": "list"})),
    path("cart/checkout/", CartViewSet.as_view({"post": "checkout"})),
    path("cart/<int:product_id>/", CartViewSet.as_view({"post": "add", "delete": "remove"})),
=======
    path("orders/<int:pk>/cancel", OrderViewSet.as_view({"post": "cancel"})),
>>>>>>> main
]
