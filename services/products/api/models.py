import uuid

from django.db import models
from django.db.models import F


class ColourChoices(models.TextChoices):
    WHITE = "white", "White"
    BLACK = "black", "Black"
    RED = "red", "Red"


class TypeChoices(models.TextChoices):
    NO_TYPE = "NUL", "NUL"
    PHONE = "phone", "Phone"
    LAPTOP = "laptop", "Laptop"
    TABLET = "tablet", "Tablet"


class SizeChoices(models.TextChoices):
    SMALL = "small", "Small"
    MEDIUM = "medium", "Medium"
    LARGE = "large", "Large"


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "api_products"


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING, related_name="product_variant")
    colour = models.CharField(max_length=30, choices=ColourChoices.choices, default=ColourChoices.WHITE)
    size = models.CharField(max_length=10, choices=SizeChoices.choices, default=SizeChoices.MEDIUM)
    type = models.CharField(max_length=50, choices=TypeChoices.choices, default=TypeChoices.NO_TYPE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sku = models.CharField(max_length=21, unique=True)

    def _generate_sku(self):
        prefix = str(self.type)[:3].upper()
        colour_code = str(self.colour)[:3].upper()
        unique = uuid.uuid4().hex[:6].upper()
        return f"{prefix}-{colour_code}-{unique}"

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = self._generate_sku()
        super().save(*args, **kwargs)

    class Meta:
        db_table = "api_products_variant"


class ProductVariantInventory(models.Model):
    product_variant = models.OneToOneField(
        ProductVariant, on_delete=models.DO_NOTHING, related_name="product_variant_inventory"
    )
    quantity_available = models.PositiveIntegerField(default=0)
    quantity_reserved = models.PositiveIntegerField(default=0)

    def reserve(self, qty: int) -> bool:
        """
        if quantity avaliable is large than reserved, reserve the qty unless it exceeds quantity avaliable
        """
        updated = ProductVariantInventory.objects.filter(
            pk=self.pk, quantity_available__gte=F("quantity_reserved") + qty
        ).update(quantity_reserved=F("quantity_reserved") + qty)

        return updated == 1

    def unreserve(self, qty: int) -> bool:
        """
        unreserve quantity from reserved
        """
        updated = ProductVariantInventory.objects.filter(pk=self.pk, quantity_reserved__gte=qty).update(
            quantity_reserved=F("quantity_reserved") - qty
        )

        return updated == 1

    class Meta:
        db_table = "api_products_variant_inventory"
