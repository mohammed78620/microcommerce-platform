from django.db import models
from rest_framework import serializers


class Cart(models.Model):
    user_id = models.IntegerField(db_index=True, unique=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="cart_items")
    product_id = models.IntegerField(db_index=True)
    quantity = models.PositiveIntegerField(default=1)


class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ["id", "product_id", "quantity"]


class CartSerializer(serializers.ModelSerializer):
    cart_items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "user_id", "cart_items"]


class Order(models.Model):
    OPEN = "Open"
<<<<<<< HEAD
    CONFIRMED = "Confirmed"
    CLOSE = "Close"
    REFUNDED = "Refunded"
=======
    CLOSE = "Close"
>>>>>>> main
    CANCELLED = "Cancelled"

    STATUS_CHOICES = [
        (OPEN, "Open"),
        (CONFIRMED, "Confirmed"),
        (REFUNDED, "Refunded"),
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


class Payment(models.Model):
    PENDING = "Pending"
    UNPAID = "Unpaid"
    REFUNDED = "Refunded"
    COMPLETE = "Complete"
    PAYMENT_CHOICES = [(PENDING, "Pending"), (REFUNDED, "Refunded"), (UNPAID, "Unpaid"), (COMPLETE, "Complete")]

    order_id = models.OneToOneField(Order, on_delete=models.DO_NOTHING)
    intent_id = models.CharField(unique=True)
    total = models.PositiveBigIntegerField(default=0)
    currency = models.CharField(max_length=3, default="gbp")
    status = models.CharField(max_length=8, choices=PAYMENT_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
