from django.urls import path
from .views import ProductViewSet, ReserveStockView, BulkReserveStockView, ProductCategoryTagViewSet

urlpatterns = [
    path("products/", ProductViewSet.as_view({"get": "list", "post": "create"})),
    path("products/search/", ProductViewSet.as_view({"post": "search"})),
    path("products/reserve/<int:product_id>", ReserveStockView.as_view()),
    path("products/bulk_reserve/", BulkReserveStockView.as_view()),
    path("products/category/", ProductCategoryTagViewSet.as_view({"get": "list_categories"})),
    path("products/tag/", ProductCategoryTagViewSet.as_view({"get": "list_tags"})),
    path("products/category/<str:category_slug>/products/", ProductCategoryTagViewSet.as_view({"get": "get_products"})),
    path(
        "products/<int:product_id>/<int:variant_id>/",
        ProductViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}),
    ),
]
