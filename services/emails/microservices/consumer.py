import json
import requests
from decimal import Decimal
from typing import Dict, Tuple, Union
import pika, sys, os
from django.db import transaction
from django.core.mail import send_mail
from decimal import Decimal
from emails import settings
from common.utils.clients import APIClient


def send_order_email(ch, method, properties, body):
    order_items_message = json.loads(body)
    order_items = order_items_message["order_items"]
    token = order_items_message["token"]
    api_client = APIClient(token)

    # call auth_service to get user
    user_id = order_items_message["user_id"]
    status, user_details = api_client.get_user(user_id)
    if not status:
        print("Failed to send email because of user")
        return
    recipient_email = user_details["email"]
    first_name = user_details["first_name"]
    last_name = user_details["last_name"]

    # Build the email body
    total = Decimal("0")
    lines = [
        f"Hello {first_name} {last_name},",
        "",
        "Thank you for your order! Here is your order summary:",
        "",
        "Order Summary",
        "=" * 30,
    ]
    for item in order_items:
        status, product = api_client.get_product(product_id=item["product_id"])
        if not status:
            print("Failed to send email because of product")
            return
        price = Decimal(str(product["price"]))
        quantity = Decimal(str(item["quantity"]))
        item_total = price * quantity
        total += item_total
        lines.append(f"Product: {product['name']} | Qty: {item['quantity']} | Total: £{item_total:.2f}")

    lines.append("=" * 30)
    lines.append(f"Order Total: £{total:.2f}")
    lines.append("")
    lines.append("Thanks for shopping with us!")

    body = "\n".join(lines)

    send_mail(
        subject="Order Confirmation #",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient_email],
        fail_silently=False,
    )


def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq"))
    channel = connection.channel()

    channel.queue_declare(queue="release-stock", durable=True, arguments={"x-queue-type": "quorum"})
    channel.queue_declare(queue="send-order-email", durable=True, arguments={"x-queue-type": "quorum"})

    channel.basic_consume(queue="send-order-email", on_message_callback=send_order_email, auto_ack=True)

    print(" [*] Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
