from django.urls import path
from .views import OrderViewSet

urlpatterns = [
    path("orders/", OrderViewSet.as_view({"get": "list", "post": "create"})),
    path("orders/<int:pk>/cancel", OrderViewSet.as_view({"post": "cancel"})),
]
