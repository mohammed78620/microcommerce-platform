import json
from typing import Dict, List

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Prefetch
from django.db import transaction
from rest_framework.exceptions import APIException
from rest_framework.request import Request
from django.contrib.postgres.search import SearchVector
from django.core.paginator import Paginator
from common.utils import CachedPaginator, flatten_subtree, get_tags, get_tree
from django.shortcuts import get_object_or_404

from .models import Product, ProductVariantInventory, ProductVariant, Category, Tag
from .serializers import ProductSerializer, ProductVariantSerializer, CategorySerializer, TagSerializer


class InsufficientStockError(APIException):
    status_code = 400
    default_detail = "Insufficient stock."
    default_code = "insufficient_stock"


class ProductViewSet(viewsets.ViewSet):
    paginator_class = CachedPaginator

    def list(self, request):
        page_size = int(request.query_params.get("limit", 10))
        page_number = int(request.query_params.get("page_number", 1))
        cache_key = f"products_per_page"
        products = Product.objects.all().prefetch_related("product_variant").order_by("name")

        paginator = self.paginator_class(object_list=products, per_page=page_size, cache_key=cache_key)
        page_obj = paginator.page(page_number)
        serializer = ProductSerializer(page_obj, many=True)
        response_data = {
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "next": page_obj.has_next(),
            "previous": page_obj.has_previous(),
            "results": list(serializer.data),
        }
        return Response(
            response_data,
            status=status.HTTP_200_OK,
        )

    def create(self, request, quantity_avaliable):
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()

        ProductVariantInventory.objects.create(product=product, quantity_avaliable=quantity_avaliable)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, product_id, variant_id):
        product = get_object_or_404(Product, id=product_id)
        product_variant = get_object_or_404(ProductVariant, pk=variant_id, product=product_id)
        data = ProductSerializer(product).data
        data["product_variant"] = ProductVariantSerializer(product_variant).data
        return Response(data)

    def update(self, request, pk=None):
        product = Product.objects.get(id=pk)
        serializer = ProductSerializer(instance=product, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, pk=None):
        product = Product.objects.get(id=pk)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def search(self, request: Request):
        """
        search for relevant product based on query


        Returns:
            List[Dict]: List of products
        """
        page_size = request.query_params.get("limit")
        page_number = request.query_params.get("page_number")
        body = json.loads(request.body)
        search_query = body.get("search")
        cache_key = f"product_search_{search_query}"
        products = (
            Product.objects.annotate(search=SearchVector("name", "description"))
            .filter(search=search_query)
            .order_by("-created_at")
        )

        if not search_query or search_query is None:
            return Response({"error": "No search query"}, status=status.HTTP_400_BAD_REQUEST)

        paginator = self.paginator_class(object_list=products, per_page=page_size, cache_key=cache_key)
        page_obj = paginator.page(page_number)

        serializer = ProductSerializer(page_obj, many=True)
        return Response(
            {
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": page_obj.has_next(),
                "previous": page_obj.has_previous(),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class ProductCategoryTagViewSet(viewsets.ViewSet):
    paginator_class = CachedPaginator

    def list_categories(self, request):
        limit = int(request.query_params["limit"])
        categories = Category.objects.all()[:limit]
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def list_tags(self, request):
        limit = int(request.query_params["limit"])
        tag = Tag.objects.all()[:limit]
        serializer = TagSerializer(tag, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_products(self, request, category_slug):
        page_size = int(request.query_params.get("limit", 10))
        page_number = int(request.query_params.get("page_number", 1))
        tags: str = request.query_params.get("tags")

        try:
            category = Category.objects.get(slug=category_slug)
        except Category.DoesNotExist:
            return Response({"detail": "Category not found."}, status=status.HTTP_404_NOT_FOUND)

        if tags:
            tags = tags.split(",")
            try:
                tag_ids = get_tags(tags)
            except Tag.DoesNotExist:
                return Response(
                    {"count": 0, "total_pages": 0, "next": False, "previous": False, "results": []},
                    status=status.HTTP_200_OK,
                )

        tags_key = ",".join(sorted(tags)) if tags else "none"
        cache_key = f"products_{category_slug}_page_{page_number}_size_{page_size}_tags_{tags_key}"

        category = Category.objects.get(slug=category_slug)
        sub_tree = get_tree(category=category)
        categories = flatten_subtree(sub_tree)
        category_ids = [c.pk for c in categories]

        if tags:
            products = (
                Product.objects.filter(
                    product_variant__category_id__in=category_ids,
                    product_variant__tags__id__in=tag_ids,
                )
                .prefetch_related(
                    Prefetch(
                        "product_variant",
                        queryset=ProductVariant.objects.filter(
                            category_id__in=category_ids,
                            tags__id__in=tag_ids,
                        )
                        .select_related("category")
                        .prefetch_related(
                            Prefetch(
                                "tags",
                                queryset=Tag.objects.filter(id__in=tag_ids),
                            )
                        )
                        .distinct(),
                    )
                )
                .distinct()
            )
        else:
            products = (
                Product.objects.filter(
                    product_variant__category_id__in=category_ids,
                )
                .prefetch_related(
                    Prefetch(
                        "product_variant",
                        queryset=ProductVariant.objects.filter(
                            category_id__in=category_ids,
                        ).select_related("category"),
                    )
                )
                .distinct()
            )

        paginator = self.paginator_class(object_list=products, per_page=page_size, cache_key=cache_key)
        page_obj = paginator.page(page_number)
        serializer = ProductSerializer(page_obj, many=True)
        response_data = {
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "next": page_obj.has_next(),
            "previous": page_obj.has_previous(),
            "results": list(serializer.data),
        }
        return Response(response_data, status=status.HTTP_200_OK)


class ReserveStockView(APIView):
    def post(self, request, product_id):
        """
        reserve a specific quantity for a product in `api_products_inventory` table
        """
        payload = json.loads(request.body)
        qty = payload["quantity"]
        variant_id = payload["variant_id"]
        try:
            product_variant_inventory: ProductVariantInventory = ProductVariantInventory.objects.get(
                product_variant__pk=variant_id,
                product_variant__product__pk=product_id,
            )
        except Product.DoesNotExist:
            Response("Product does not exist", status=status.HTTP_404_NOT_FOUND)

        updated = product_variant_inventory.reserve(qty)
        if not updated:
            return Response(f"No avaliable stock for product {product_id}", status=status.HTTP_400_BAD_REQUEST)

        return Response(updated, status=status.HTTP_201_CREATED)


class BulkReserveStockView(APIView):
    def post(self, request):
        """
        Bulk reserve a list of products and make sure the database is a transaction
        """
        items = request.data["items"]
        try:
            with transaction.atomic():
                for item in items:
                    product_id, variant_id = item["product_id"], item["variant_id"]
                    product_variant_inventory: ProductVariantInventory = ProductVariantInventory.objects.get(
                        product_variant__pk=variant_id,
                        product_variant__product__pk=product_id,
                    )
                    success = product_variant_inventory.reserve(item["quantity"])
                    if not success:
                        raise InsufficientStockError(item["product_id"])
        except Product.DoesNotExist as e:
            return Response({"success": False, "reason": "not_found"}, status=status.HTTP_404_NOT_FOUND)
        except InsufficientStockError as e:
            return Response(
                {"success": False, "reason": "insufficient_stock", "product_id": e.product_id},
                status=status.HTTP_409_CONFLICT,
            )

        return Response({"success": True}, status=status.HTTP_200_OK)
