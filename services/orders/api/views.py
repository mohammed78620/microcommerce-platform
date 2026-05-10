from typing import Dict, List
import json

import requests

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny

from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer
from microservices.producer import publish_message


def get_jwt_token(request):
    """
    return jwt token from request
    """
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ")[1]
    return token


def bulk_reserve_order(token, items_data: List[Dict[str, int]]):

    try:
        # TODO: move URL to environment variable
        # TODO: authenticate the token using JWT_SECRET.
        # Make sure JWT_SECRET the same in auth_service and orders
        response = requests.post(
            "http://products:8002/api/products/bulk_reserve/",
            json={"items": items_data},
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
            timeout=5,
        )
    except requests.exceptions.RequestException:
        raise AuthenticationFailed("Auth service unreachable")

    if response.status_code == 409:
        data = response.json()
        return False, data.get("product_id")

    response.raise_for_status()
    return True, None


class OrderViewSet(viewsets.ViewSet):
    def list(self, request):
        orders = Order.objects.all()
        serializer = OrderSerializer(orders, many=True)
        data = serializer.data
        for i, item in enumerate(data):
            order_id = item["id"]
            order_items = Order.objects.get(id=order_id).order_items.all()
            order_item_serializer = OrderItemSerializer(order_items, many=True)
            data[i]["order_items"] = order_item_serializer.data

        return Response(data, status=status.HTTP_200_OK)

    def create(self, request):
        user = request.user
        token = get_jwt_token(request)

        order_data = request.data
        if not order_data:
            return Response("no order data", status=status.HTTP_400_BAD_REQUEST)
        order_items_data = order_data.pop("order_items", [])

        if not order_items_data:
            return Response("no order data", status=status.HTTP_400_BAD_REQUEST)

        # reserve products
        success, failed_product_id = bulk_reserve_order(token, order_items_data)

        if not success:
            raise ValueError(f"Product is out of stock {failed_product_id}")

        # create order and order items
        try:
            with transaction.atomic():
                order = Order.objects.create(user_id=user.id)
                order_item_bulk_create = []
                for item in order_items_data:
                    order_item = OrderItem(order=order, product_id=item["product_id"], quantity=item["quantity"])
                    order_item_bulk_create.append(order_item)
                num_created = OrderItem.objects.bulk_create(order_item_bulk_create)
                if len(num_created) != len(order_item_bulk_create):
                    raise Exception("number of order items created not matching value returned by bulk_create")
        except Exception:
            # if order fails release product reservation via messages
            publish_message(order_items_data, "release-product")
            return Response("Failed to create order", status=status.HTTP_400_BAD_REQUEST)

        # send email if order created
        email_payload = {"user_id": user.id, "token": token, "order_items": order_items_data}
        publish_message(email_payload, "send-order-email")

        return Response("Order created", status=status.HTTP_201_CREATED)

    def cancel(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response("order does not exist", status=status.HTTP_404_NOT_FOUND)
        with transaction.atomic():
            order.status = Order.CANCELLED
            order.save()

        return Response(f"Order {pk} has been cancelled", status=status.HTTP_200_OK)
