from django.core.management.base import BaseCommand

from api.models import Product


class Command(BaseCommand):
    help = "Seed initial product data"

    def handle(self, *args, **kwargs):
        products = [
            {"name": "Widget A", "price": "9.99", "quantity_available": 100},
            {"name": "Widget B", "price": "19.99", "quantity_available": 50},
        ]

        for data in products:
            product, created = Product.objects.get_or_create(
                name=data["name"],
                defaults={
                    "price": data["price"],
                    "quantity_available": data["quantity_available"],
                },
            )
            if created:
                self.stdout.write(f"Created {product.name}")
            else:
                self.stdout.write(f"Skipped {product.name} — already exists")
