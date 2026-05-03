from django.urls import path
from .views import ProductViewSet, ReserveStockView, BulkReserveStockView

urlpatterns = [
    path("products/", ProductViewSet.as_view({"get": "retrieve", "post": "create"})),
    path("products/reserve/<int:product_id>", ReserveStockView.as_view()),
    path("products/bulk_reserve/", BulkReserveStockView.as_view()),
    path("products/<str:pk>/", ProductViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"})),
]
