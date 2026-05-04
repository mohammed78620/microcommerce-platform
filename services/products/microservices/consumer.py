import json
import pika, sys, os
from django.db import transaction

from api.models import Product


def release_stock(ch, method, properties, body):
    products_message = json.loads(body)
    try:
        with transaction.atomic():
            for product_message in products_message:
                products = Product.objects.select_for_update().get(pk=product_message["product_id"])
                products.unreserve(product_message["quantity"])
    except Product.DoesNotExist as e:
        return {"success": False, "reason": "not_found"}


def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq"))
    channel = connection.channel()

    channel.queue_declare(queue="release-stock", durable=True, arguments={"x-queue-type": "quorum"})

    channel.basic_consume(queue="release-stock", on_message_callback=release_stock, auto_ack=True)

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
