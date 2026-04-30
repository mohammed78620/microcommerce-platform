from django.db import models
from django.db.models import F


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    quantity_available = models.PositiveIntegerField(default=0)
    quantity_reserved = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "api_products"

    def reserve(self, qty: int) -> bool:

        updated = Product.objects.filter(pk=self.pk, quantity_available__gte=F("quantity_reserved") + qty).update(
            quantity_reserved=F("quantity_reserved") + qty
        )

        return updated == 1
