import pika
import json


def publish_release_stock(message: dict, host: str = "rabbitmq"):
    # [{"product_id": 1, "quantity": 5}]
    connection = pika.BlockingConnection(pika.ConnectionParameters(host))
    channel = connection.channel()

    channel.queue_declare(
        queue="release-stock",
        durable=True,
        arguments={"x-queue-type": "quorum"},
    )

    channel.basic_publish(
        exchange="",
        routing_key="release-stock",
        body=json.dumps(message).encode("utf-8"),
        properties=pika.BasicProperties(
            content_type="application/json",
            delivery_mode=2,
        ),
    )

    print(f" [x] Sent {message}")

    connection.close()


publish_release_stock([{"product_id": 1, "quantity": 2}])
