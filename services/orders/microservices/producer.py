import pika
import json
from orders import settings

try:
    connection = pika.BlockingConnection(pika.ConnectionParameters(settings.RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(
        queue="release-stock",
        durable=True,
        arguments={"x-queue-type": "quorum"},
    )
    channel.queue_declare(
        queue="send-order-email",
        durable=True,
        arguments={"x-queue-type": "quorum"},
    )
except Exception:
    print("Failed to estabilish conection to rabbitmq")


def publish_message(message: dict, queue: str = None):
    channel.basic_publish(
        exchange="",
        routing_key=queue,
        body=json.dumps(message).encode("utf-8"),
        properties=pika.BasicProperties(
            content_type="application/json",
            delivery_mode=2,
        ),
    )
    print(f" [x] Sent {message}")
