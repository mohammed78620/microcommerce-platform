import random

from django.core.management.base import BaseCommand

from api.models import (
    Product,
    ProductVariant,
    ProductVariantInventory,
    Category,
    Tag,
    ColourChoices,
    SizeChoices,
    TypeChoices,
)


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

    COLOURS = [c.value for c in ColourChoices]
    SIZES = [s.value for s in SizeChoices]
    TYPES = [t.value for t in TypeChoices if t != TypeChoices.NO_TYPE]

    TAGS = [
        "sale",
        "flash-sale",
        "clearance",
        "bundle-deal",
        "new-arrival",
        "bestseller",
        "limited-edition",
        "back-in-stock",
        "coming-soon",
    ]

    def handle(self, *args, **kwargs):
        created_count = 0
        skipped_count = 0

        # Categories
        electronics, _ = Category.objects.get_or_create(name="Electronics", slug="electronics")
        phones, _ = Category.objects.get_or_create(name="Phones", slug="phones", defaults={"parent": electronics})
        smartphones, _ = Category.objects.get_or_create(
            name="Smartphones", slug="smartphones", defaults={"parent": phones}
        )
        laptops, _ = Category.objects.get_or_create(name="Laptops", slug="laptops", defaults={"parent": electronics})
        tablets, _ = Category.objects.get_or_create(name="Tablets", slug="tablets", defaults={"parent": electronics})

        # Map type → appropriate categories so variants make sense
        type_category_map = {
            TypeChoices.PHONE.value: [phones, smartphones],
            TypeChoices.LAPTOP.value: [laptops],
            TypeChoices.TABLET.value: [tablets],
        }

        # Tags
        tags = []
        for tag_name in self.TAGS:
            tag, _ = Tag.objects.get_or_create(name=tag_name, slug=tag_name)
            tags.append(tag)

        for i in range(1, 101):
            name = (
                f"{random.choice(self.ADJECTIVES)} "
                f"{random.choice(self.NOUNS)} "
                f"{random.choice(self.VARIANTS)} {i}"
            )
            product, created = Product.objects.get_or_create(
                name=name,
                defaults={"description": f"A high-quality {name.lower()}."},
            )

            for _ in range(3):
                variant_type = random.choice(self.TYPES)
                category = random.choice(type_category_map[variant_type])

                product_variant, variant_created = ProductVariant.objects.get_or_create(
                    product=product,
                    colour=random.choice(self.COLOURS),
                    size=random.choice(self.SIZES),
                    type=variant_type,
                    category=category,
                    defaults={
                        "price": round(random.uniform(4.99, 299.99), 2),
                    },
                )

                if not variant_created:
                    continue

                # Assign 1–3 random tags
                product_variant.tags.set(random.sample(tags, k=random.randint(1, 3)))

                ProductVariantInventory.objects.get_or_create(
                    product_variant=product_variant,
                    defaults={"quantity_available": random.randint(0, 500)},
                )

            if created:
                created_count += 1
                self.stdout.write(f"Created: {product.name}")
            else:
                skipped_count += 1
                self.stdout.write(f"Skipped: {product.name} — already exists")

        self.stdout.write(self.style.SUCCESS(f"\nDone — {created_count} created, {skipped_count} skipped."))
