import random

from django.core.management.base import BaseCommand

from api.models import Product


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
                defaults={
                    "price": round(random.uniform(4.99, 299.99), 2),
                    "quantity_available": random.randint(0, 500),
                },
            )

            if created:
                created_count += 1
                self.stdout.write(f"Created: {product.name}")
            else:
                skipped_count += 1
                self.stdout.write(f"Skipped: {product.name} — already exists")

        self.stdout.write(self.style.SUCCESS(f"\nDone — {created_count} created, {skipped_count} skipped."))
