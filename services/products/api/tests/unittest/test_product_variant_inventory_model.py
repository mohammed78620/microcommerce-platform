from django.test import TestCase

from api.models import Product, ProductVariant, ProductVariantInventory


class ProductInventoryTestCase(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name="product_1")
        self.variant = ProductVariant.objects.create(product=self.product, price="9.99", colour="blue")

    def test_inventory_does_not_exist_before_creation(self):
        with self.assertRaises(ProductVariantInventory.DoesNotExist):
            ProductVariantInventory.objects.get(product_variant=self.variant)

    def test_reserved_defaults_to_zero_on_creation(self):
        inventory = ProductVariantInventory.objects.create(product_variant=self.variant, quantity_available=20)
        self.assertEqual(inventory.quantity_reserved, 0)

    def test_reserve_succeeds_when_qty_within_available(self):
        inventory = ProductVariantInventory.objects.create(product_variant=self.variant, quantity_available=20)

        result = inventory.reserve(9)

        inventory.refresh_from_db()
        self.assertTrue(result)
        self.assertEqual(inventory.quantity_reserved, 9)

    def test_reserve_fails_when_qty_exceeds_available(self):
        inventory = ProductVariantInventory.objects.create(product_variant=self.variant, quantity_available=20)

        result = inventory.reserve(21)

        inventory.refresh_from_db()
        self.assertFalse(result)
        self.assertEqual(inventory.quantity_reserved, 0)

    def test_reserve_succeeds_exactly_at_available_boundary(self):
        inventory = ProductVariantInventory.objects.create(product_variant=self.variant, quantity_available=20)

        result = inventory.reserve(20)

        inventory.refresh_from_db()
        self.assertTrue(result)
        self.assertEqual(inventory.quantity_reserved, 20)

    def test_reserve_fails_when_existing_reserved_plus_qty_exceeds_available(self):
        inventory = ProductVariantInventory.objects.create(
            product_variant=self.variant, quantity_available=20, quantity_reserved=15
        )

        result = inventory.reserve(6)  # 15 + 6 = 21 > 20

        inventory.refresh_from_db()
        self.assertFalse(result)
        self.assertEqual(inventory.quantity_reserved, 15)

    def test_unreserve_succeeds_when_qty_within_reserved(self):
        inventory = ProductVariantInventory.objects.create(
            product_variant=self.variant, quantity_available=20, quantity_reserved=10
        )

        result = inventory.unreserve(10)

        inventory.refresh_from_db()
        self.assertTrue(result)
        self.assertEqual(inventory.quantity_reserved, 0)

    def test_unreserve_fails_when_qty_exceeds_reserved(self):
        inventory = ProductVariantInventory.objects.create(
            product_variant=self.variant, quantity_available=20, quantity_reserved=10
        )

        result = inventory.unreserve(20)

        inventory.refresh_from_db()
        self.assertFalse(result)
        self.assertEqual(inventory.quantity_reserved, 10)

    def test_unreserve_partial_amount(self):
        inventory = ProductVariantInventory.objects.create(
            product_variant=self.variant, quantity_available=20, quantity_reserved=10
        )

        result = inventory.unreserve(4)

        inventory.refresh_from_db()
        self.assertTrue(result)
        self.assertEqual(inventory.quantity_reserved, 6)

    def test_unreserve_succeeds_exactly_at_reserved_boundary(self):
        inventory = ProductVariantInventory.objects.create(
            product_variant=self.variant, quantity_available=20, quantity_reserved=5
        )

        result = inventory.unreserve(5)

        inventory.refresh_from_db()
        self.assertTrue(result)
        self.assertEqual(inventory.quantity_reserved, 0)
