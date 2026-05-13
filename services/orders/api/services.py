from typing import Dict, List


import requests


from django.db import transaction

from rest_framework.exceptions import AuthenticationFailed

from .models import Order, OrderItem
from microservices.producer import publish_message
from orders import settings


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
        response = requests.post(
            f"{settings.PRODUCTS_SERVICE_URL}api/products/bulk_reserve/",
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


def create_order_from_items(user, token, order_items_data: List[Dict[str, int]]):
    success, failed_product_id = bulk_reserve_order(token, order_items_data)
    if not success:
        raise ValueError(f"Product out of stock: {failed_product_id}")

    try:
        with transaction.atomic():
            order = Order.objects.create(user_id=user.id)
            OrderItem.objects.bulk_create(
                [
                    OrderItem(order=order, product_id=item["product_id"], quantity=item["quantity"])
                    for item in order_items_data
                ]
            )
    except Exception as e:
        publish_message(order_items_data, "release-product")
        raise e

    publish_message({"user_id": user.id, "token": token, "order_items": order_items_data}, "send-order-email")
    return order
