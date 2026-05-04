import json

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views import View
from django.db import transaction
from rest_framework.exceptions import APIException

from .models import Product
from .serializers import ProductSerializer


class InsufficientStockError(APIException):
    status_code = 400
    default_detail = "Insufficient stock."
    default_code = "insufficient_stock"


class ProductViewSet(viewsets.ViewSet):
    def list(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        product = Product.objects.get(id=pk)
        serializer = ProductSerializer(product)
        return Response(serializer.data)

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


class ReserveStockView(APIView):
    def post(self, request, product_id):
        payload = json.loads(request.body)
        qty = payload["quantity"]
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            Response("Product does not exist", status=status.HTTP_404_NOT_FOUND)

        updated = product.reserve(qty)
        if not updated:
            return Response(f"No avaliable stock for product {product_id}", status=status.HTTP_400_BAD_REQUEST)

        return Response(updated, status=status.HTTP_201_CREATED)


class BulkReserveStockView(APIView):
    def post(self, request):
        # [{"product_id": 1, "quantity": 2}, {"product_id": 2, "quantity": 1}]
        items = request.data["items"]
        try:
            with transaction.atomic():
                for item in items:
                    product = Product.objects.select_for_update().get(pk=int(item["product_id"]))
                    success = product.reserve(item["quantity"])
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
