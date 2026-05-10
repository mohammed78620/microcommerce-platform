from decimal import Decimal
from typing import Dict, List
import json
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


def calculate_total(order_items_data: List[Dict[str, int]], token: str) -> int:
    try:
        # TODO: move URL to environment variable
        total = Decimal("0")
        for item in order_items_data:
            product_id = item["product_id"]
            response = requests.get(
                f"http://products:8002/api/products/{product_id}/",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                },
                timeout=5,
            )
            response = response.json()
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
            f"http://products:8002/api/products/{product_id}/",
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
        except ValueError as e:
            return Response(str(e), status=409)
        except Exception:
            return Response("Failed to create order", status=400)
        total = calculate_total(order_items_data, get_jwt_token(request))
        intent = stripe.PaymentIntent.create(amount=total, currency="gbp", metadata={"order_id": 1})
        Payment.objects.create(
            order_id=order,
            intent_id=intent.id,
            total=total,
        )
        cart.delete()

        return Response({"order_id": 1, "client_secret": intent.client_secret}, status=201)
