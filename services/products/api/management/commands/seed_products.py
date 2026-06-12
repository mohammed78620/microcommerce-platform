import random

from django.core.management.base import BaseCommand

from api.models import Product, ProductVariant, ProductVariantInventory


class Command(BaseCommand):
    help = "Seed initial product data"

    ADJECTIVES = [
        "Premium",
        "Deluxe",
        "Ultra",
        "Pro",
        "Elite",
        "Super",
        "Mega",
        "Turbo",
        "Advanced",
        "Classic",
        "Compact",
        "Heavy-Duty",
        "Lite",
    ]

    NOUNS = [
        "Widget",
        "Gadget",
        "Gizmo",
        "Device",
        "Tool",
        "Unit",
        "Module",
        "Component",
        "Kit",
        "Pack",
        "Set",
        "System",
        "Panel",
    ]

    VARIANTS = ["Alpha", "Beta", "X", "Z", "Plus", "Max", "One", "Edge"]
    COLOUR = ["black", "red", "blue"]
    SIZE = ["Small", "Medium", "Large"]
    TYPE = ["Phone", "Laptop", "Tablet"]

    def handle(self, *args, **kwargs):
        created_count = 0
        skipped_count = 0

        for i in range(1, 101):
            name = (
                f"{random.choice(self.ADJECTIVES)} "
                f"{random.choice(self.NOUNS)} "
                f"{random.choice(self.VARIANTS)} {i}"
            )
            product, created = Product.objects.get_or_create(
                name=name,
            )
            for i in range(0, 3):

                product_variant, created = ProductVariant.objects.get_or_create(
                    product=product,
                    colour=random.choice(self.COLOUR),
                    size=random.choice(self.SIZE),
                    type=random.choice(self.TYPE),
                    defaults={
                        "price": round(random.uniform(4.99, 299.99), 2),
                    },
                )
                if not created:
                    continue
                ProductVariantInventory.objects.get_or_create(
                    product_variant=product_variant, quantity_available=random.randint(0, 500)
                )

            if created:
                created_count += 1
                self.stdout.write(f"Created: {product.name}")
            else:
                skipped_count += 1
                self.stdout.write(f"Skipped: {product.name} — already exists")

        self.stdout.write(self.style.SUCCESS(f"\nDone — {created_count} created, {skipped_count} skipped."))
