import pika
import json
import os
from orders import settings

try:
    credentials = pika.PlainCredentials(
        username=os.environ.get("RABBITMQ_USER", "guest"),
        password=os.environ.get("RABBITMQ_PASSWORD", "guest"),
    )
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=os.environ.get("RABBITMQ_HOST", "rabbitmq"),
            credentials=credentials,
        )
    )
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
