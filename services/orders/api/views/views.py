from decimal import Decimal
from typing import Dict, List
from collections import defaultdict
import stripe

import requests

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from ..models import Order, OrderItem, Cart, CartItem, Payment, CartItemSerializer
from ..serializers import OrderSerializer, OrderItemSerializer
from ..services import create_order_from_items, get_jwt_token
from microservices.producer import publish_message
from orders import settings


def get_product(product_id: int, token: str) -> Dict:
    try:
        response = requests.get(
            f"{settings.PRODUCTS_SERVICE_URL}api/products/{product_id}/",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
            timeout=5,
        )
        response = response.json()

    except requests.exceptions.RequestException:
        raise AuthenticationFailed("Auth service unreachable")
    return response


def calculate_total(order_items_data: List[Dict[str, int]], token: str) -> int:
    try:
        total = Decimal("0")
        for item in order_items_data:
            product_id = item["product_id"]
            response = get_product(product_id=product_id, token=token)
            price = Decimal(str(response["price"]))
            quantity = Decimal(str(item["quantity"]))
            item_total = price * quantity
            total += item_total
    except requests.exceptions.RequestException:
        raise AuthenticationFailed("Auth service unreachable")
    return int(total * 100)


def get_product(product_id: int, token: str) -> Dict:
    try:
        response = requests.get(
            f"{settings.PRODUCTS_SERVICE_URL}api/products/{product_id}/",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
            timeout=5,
        )
    except requests.exceptions.RequestException:
        raise AuthenticationFailed("Auth service unreachable")
    return response.json()


class OrderViewSet(viewsets.ViewSet):
    def list(self, request, user_id: int):
        """
        get orders from specific user

        Args:
            user_id (int): the users id

        Returns:
            List[List[Dict]]: return a list of orders where each order contains the products and quantity
        """
        order_items = OrderItem.objects.filter(order__user_id=user_id).select_related("order")

        if not order_items.count() > 0:
            return Response([], status=status.HTTP_200_OK)

        token = get_jwt_token(request)
        product_ids = {item.product_id for item in order_items}
        products = {pid: get_product(product_id=pid, token=token) for pid in product_ids}

        # Get order statuses
        orders = Order.objects.filter(user_id=user_id)

        order_statuses = {order.id: order.status for order in orders}

        orders_map = defaultdict(list)
        for item in order_items:
            product = products.get(item.product_id, {})
            orders_map[item.order_id].append(
                {
                    **OrderItemSerializer(item).data,
                    "name": product.get("name"),
                    "price": float(product.get("price")),
                }
            )

        # Add order status to each order
        result = []
        for order_id, items in orders_map.items():
            result.append({"order_id": order_id, "status": order_statuses.get(order_id), "items": items})

        return Response(result, status=status.HTTP_200_OK)

    def create(self, request):
        order_items_data = request.data.pop("order_items", [])
        if not order_items_data:
            return Response("no order data", status=400)
        try:
            create_order_from_items(request.user, get_jwt_token(request), order_items_data)
        except ValueError as e:
            return Response(str(e), status=409)
        except Exception:
            return Response("Failed to create order", status=400)
        return Response("Order created", status=201)

    def cancel(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response("order does not exist", status=status.HTTP_404_NOT_FOUND)
        with transaction.atomic():
            order.status = Order.CANCELLED
            order.save()

        return Response(f"Order {pk} has been cancelled", status=status.HTTP_200_OK)


class CartViewSet(viewsets.ViewSet):
    def add(self, request, product_id):
        # if user has no cart create cart with product
        # if product exists increment quantity
        user = request.user

        cart, _ = Cart.objects.get_or_create(user_id=user.id)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product_id=product_id)
        if not created:
            cart_item.quantity += 1
            cart_item.save()

        return Response(f"added {product_id} to cart", status=status.HTTP_201_CREATED)

    def remove(self, request, product_id):
        # decrement products quantity or remove if 0
        user = request.user
        cart = Cart.objects.get(user_id=user.id)
        try:
            cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
        except CartItem.DoesNotExist:
            Response(f"product {product_id} does not exist", status=status.HTTP_400_BAD_REQUEST)
        cart_item.quantity -= 1
        if cart_item.quantity == 0:
            cart_item.delete()
            Response(f"removed {product_id} cart", status=status.HTTP_201_CREATED)
        else:
            cart_item.save()
        return Response(f"removed one {product_id} cart", status=status.HTTP_201_CREATED)

    def list(self, request):
        user = request.user
        cart, _ = Cart.objects.get_or_create(user_id=user.id)
        cart_items = CartItem.objects.filter(cart=cart)

        token = get_jwt_token(request)
        items = []
        for item in cart_items:
            product = get_product(product_id=item.product_id, token=token)
            items.append(
                {**CartItemSerializer(item).data, "price": float(product["price"]), "name": product["name"]},
            )

        return Response(items, status=status.HTTP_200_OK)

    def checkout(self, request):
        # from cart convert items into orderitems List[Dict[str, int]] and pass to func create_order_from_items
        user = request.user
        cart = Cart.objects.get(user_id=user.id)
        cart_items = CartItem.objects.filter(cart=cart)
        if not cart_items.count() > 0:
            return Response("Cart has no items", status=status.HTTP_400_BAD_REQUEST)
        order_items_data = [
            {"product_id": cart_item.product_id, "quantity": cart_item.quantity} for cart_item in cart_items
        ]
        try:
            order = create_order_from_items(user=user, token=get_jwt_token(request), order_items_data=order_items_data)
            total = calculate_total(order_items_data, get_jwt_token(request))
            intent = stripe.PaymentIntent.create(amount=total, currency="gbp", metadata={"order_id": order.pk})
            Payment.objects.create(
                order_id=order,
                intent_id=intent.id,
                total=total,
            )
            cart.delete()
        except ValueError as e:
            return Response(str(e), status=409)
        except Exception as e:
            return Response(f"Failed to create order {e}", status=400)

        return Response({"order_id": 1, "client_secret": intent.client_secret}, status=201)
