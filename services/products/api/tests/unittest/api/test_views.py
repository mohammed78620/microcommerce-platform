from django.test import TestCase
from rest_framework.test import APIClient
from django.core.cache import cache

from api.models import Category, Tag, Product, ProductVariant, ProductVariantInventory

CATEGORIES_URL = "/api/products/category/"
TAGS_URL = "/api/products/tag/"


def category_products_url(slug):
    return f"/api/products/category/{slug}/products/"


class ProductCategoryTagViewSetTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

        # Category tree
        self.electronics = Category.objects.create(name="Electronics", slug="electronics")
        self.phones = Category.objects.create(name="Phones", slug="phones", parent=self.electronics)
        self.smartphones = Category.objects.create(name="Smartphones", slug="smartphones", parent=self.phones)
        self.laptops = Category.objects.create(name="Laptops", slug="laptops")

        # Tags
        self.tag_sale = Tag.objects.create(name="sale", slug="sale")
        self.tag_new = Tag.objects.create(name="new-arrival", slug="new-arrival")

        # p1 — variant in Electronics (root)
        self.p1 = Product.objects.create(name="Generic Device", description="A device.")
        self.v1 = ProductVariant.objects.create(
            product=self.p1,
            colour="black",
            size="medium",
            type="phone",
            price="49.99",
            sku="PHO-BLA-AA0001",
            category=self.electronics,
        )
        self.v1.tags.add(self.tag_sale)
        ProductVariantInventory.objects.create(product_variant=self.v1, quantity_available=10)

        # p2 — variant in Phones (child)
        self.p2 = Product.objects.create(name="Basic Phone", description="A phone.")
        self.v2 = ProductVariant.objects.create(
            product=self.p2,
            colour="red",
            size="small",
            type="phone",
            price="99.99",
            sku="PHO-RED-BB0002",
            category=self.phones,
        )
        self.v2.tags.add(self.tag_new)
        ProductVariantInventory.objects.create(product_variant=self.v2, quantity_available=5)

        # p3 — variant in Smartphones (grandchild)
        self.p3 = Product.objects.create(name="Smart Phone Pro", description="A smartphone.")
        self.v3 = ProductVariant.objects.create(
            product=self.p3,
            colour="black",
            size="large",
            type="phone",
            price="299.99",
            sku="PHO-BLA-CC0003",
            category=self.smartphones,
        )
        self.v3.tags.add(self.tag_sale)
        ProductVariantInventory.objects.create(product_variant=self.v3, quantity_available=20)

        # p4 — variant in Laptops (outside electronics subtree)
        self.p4 = Product.objects.create(name="Laptop X", description="A laptop.")
        self.v4 = ProductVariant.objects.create(
            product=self.p4,
            colour="black",
            size="large",
            type="laptop",
            price="999.99",
            sku="LAP-BLA-DD0004",
            category=self.laptops,
        )
        self.v4.tags.add(self.tag_sale)
        ProductVariantInventory.objects.create(product_variant=self.v4, quantity_available=3)

    # ─── list_categories ──────────────────────────────────────────────────────

    def test_list_categories_returns_up_to_limit(self):
        response = self.client.get(CATEGORIES_URL, {"limit": 2})
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(response.data), 2)

    def test_list_categories_limit_larger_than_total(self):
        response = self.client.get(CATEGORIES_URL, {"limit": 100})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), Category.objects.count())

    # ─── list_tags ────────────────────────────────────────────────────────────

    def test_list_tags_returns_up_to_limit(self):
        response = self.client.get(TAGS_URL, {"limit": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_list_tags_limit_larger_than_total(self):
        response = self.client.get(TAGS_URL, {"limit": 100})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), Tag.objects.count())

    # ─── get_products — no tag filter ─────────────────────────────────────────

    def test_get_products_returns_products_in_subtree(self):
        # import pdb

        # pdb.set_trace()
        response = self.client.get(category_products_url("electronics"), {"limit": 10, "page_number": 1})
        self.assertEqual(response.status_code, 200)
        ids = [p["id"] for p in response.data["results"]]
        self.assertIn(self.p1.id, ids)
        self.assertIn(self.p2.id, ids)
        self.assertIn(self.p3.id, ids)

    def test_get_products_excludes_products_outside_subtree(self):
        response = self.client.get(category_products_url("electronics"), {"limit": 10, "page_number": 1})
        self.assertEqual(response.status_code, 200)
        ids = [p["id"] for p in response.data["results"]]
        self.assertNotIn(self.p4.id, ids)

    def test_get_products_child_category_excludes_parent_only_products(self):
        # p1's variant is in Electronics root, not in Phones subtree
        response = self.client.get(category_products_url("phones"), {"limit": 10, "page_number": 1})
        self.assertEqual(response.status_code, 200)
        ids = [p["id"] for p in response.data["results"]]
        self.assertNotIn(self.p1.id, ids)
        self.assertIn(self.p2.id, ids)
        self.assertIn(self.p3.id, ids)

    def test_get_products_variants_only_from_subtree(self):
        # p1 gets a second variant in Laptops; it should still not appear under phones
        ProductVariant.objects.create(
            product=self.p1,
            colour="red",
            size="small",
            type="laptop",
            price="599.99",
            sku="LAP-RED-EE0005",
            category=self.laptops,
        )
        response = self.client.get(category_products_url("phones"), {"limit": 10, "page_number": 1})
        self.assertEqual(response.status_code, 200)
        ids = [p["id"] for p in response.data["results"]]
        self.assertNotIn(self.p1.id, ids)

    def test_get_products_invalid_slug_returns_404(self):
        # requires view to catch Category.DoesNotExist and return 404
        response = self.client.get(category_products_url("does-not-exist"), {"limit": 10, "page_number": 1})
        self.assertEqual(response.status_code, 404)

    # ─── get_products — tag filter ────────────────────────────────────────────

    def test_get_products_filtered_by_single_tag(self):
        response = self.client.get(
            category_products_url("electronics"),
            {"limit": 10, "page_number": 1, "tags": "sale"},
        )
        self.assertEqual(response.status_code, 200)
        ids = [p["id"] for p in response.data["results"]]
        self.assertIn(self.p1.id, ids)
        self.assertIn(self.p3.id, ids)
        self.assertNotIn(self.p2.id, ids)

    def test_get_products_tag_filter_excludes_outside_subtree(self):
        # p4 has the sale tag but is in Laptops, not electronics subtree
        response = self.client.get(
            category_products_url("electronics"),
            {"limit": 10, "page_number": 1, "tags": "sale"},
        )
        self.assertEqual(response.status_code, 200)
        ids = [p["id"] for p in response.data["results"]]
        self.assertNotIn(self.p4.id, ids)

    def test_get_products_multiple_tags_returns_union(self):
        response = self.client.get(
            category_products_url("electronics"),
            {"limit": 10, "page_number": 1, "tags": "sale,new-arrival"},
        )
        self.assertEqual(response.status_code, 200)
        ids = [p["id"] for p in response.data["results"]]
        self.assertIn(self.p1.id, ids)
        self.assertIn(self.p2.id, ids)
        self.assertIn(self.p3.id, ids)

    def test_get_products_nonexistent_tag_returns_empty(self):
        # requires get_tags to handle missing tags gracefully (return 200 + empty)
        response = self.client.get(
            category_products_url("electronics"),
            {"limit": 10, "page_number": 1, "tags": "does-not-exist"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], [])

    # ─── get_products — pagination ────────────────────────────────────────────

    def test_get_products_response_shape(self):
        response = self.client.get(category_products_url("electronics"), {"limit": 10, "page_number": 1})
        self.assertEqual(response.status_code, 200)
        for key in ("count", "total_pages", "next", "previous", "results"):
            self.assertIn(key, response.data)

    def test_get_products_page_size_respected(self):
        response = self.client.get(category_products_url("electronics"), {"limit": 2, "page_number": 1})
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(response.data["results"]), 2)

    def test_get_products_first_page_flags(self):
        response = self.client.get(category_products_url("electronics"), {"limit": 1, "page_number": 1})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["next"])
        self.assertFalse(response.data["previous"])

    def test_get_products_last_page_flags(self):
        total = (
            Product.objects.filter(product_variant__category__slug__in=["electronics", "phones", "smartphones"])
            .distinct()
            .count()
        )
        response = self.client.get(category_products_url("electronics"), {"limit": 1, "page_number": total})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["next"])
        self.assertTrue(response.data["previous"])
