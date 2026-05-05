from django.db import models
import uuid


class Order(models.Model):
    OPEN = "Open"
    CLOSE = "Close"
    CANCELLED = "Cancelled"

    STATUS_CHOICES = [
        (OPEN, "Open"),
        (CLOSE, "Close"),
        (CANCELLED, "Cancelled"),
    ]

    user_id = models.IntegerField(db_index=True)
    status = models.CharField(max_length=9, choices=STATUS_CHOICES, default=OPEN)

    class Meta:
        db_table = "api_order"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_items")
    product_id = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} x {self.product_title} in order {self.order.title}"

    class Meta:
        db_table = "api_orderitem"
