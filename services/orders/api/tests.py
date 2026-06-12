from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from .models import Cart, CartItem
from .views.views import CartViewSet

User = get_user_model()


class CartViewSetTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(username="testuser", password="password")
        self.view = CartViewSet.as_view(
            {
                "post": "add",
                "delete": "remove",
                "get": "list",
            }
        )

    def test_add_creates_cart_and_item_when_none_exist(self):
        request = self.factory.post("/cart/add/1/2/")
        force_authenticate(request, user=self.user)

        response = CartViewSet.as_view({"post": "add"})(request, product_id=1, variant_id=2)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Cart.objects.filter(user_id=self.user.id).exists())
        item = CartItem.objects.get(cart__user_id=self.user.id, product_id=1, variant_id=2)
        self.assertEqual(item.quantity, 1)

    def test_add_increments_quantity_when_item_already_in_cart(self):
        cart = Cart.objects.create(user_id=self.user.id)
        CartItem.objects.create(cart=cart, product_id=1, variant_id=2, quantity=1)

        request = self.factory.post("/cart/add/1/2/")
        force_authenticate(request, user=self.user)

        CartViewSet.as_view({"post": "add"})(request, product_id=1, variant_id=2)

        item = CartItem.objects.get(cart=cart, product_id=1, variant_id=2)
        self.assertEqual(item.quantity, 2)

    def test_add_reuses_existing_cart(self):
        Cart.objects.create(user_id=self.user.id)

        request = self.factory.post("/cart/add/5/3/")
        force_authenticate(request, user=self.user)

        CartViewSet.as_view({"post": "add"})(request, product_id=5, variant_id=3)

        self.assertEqual(Cart.objects.filter(user_id=self.user.id).count(), 1)

    def test_remove_decrements_quantity(self):
        cart = Cart.objects.create(user_id=self.user.id)
        CartItem.objects.create(cart=cart, product_id=1, variant_id=2, quantity=3)

        request = self.factory.delete("/cart/remove/1/2/")
        force_authenticate(request, user=self.user)

        response = CartViewSet.as_view({"delete": "remove"})(request, product_id=1, variant_id=2)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        item = CartItem.objects.get(cart=cart, product_id=1, variant_id=2)
        self.assertEqual(item.quantity, 2)

    def test_remove_deletes_item_when_quantity_reaches_zero(self):
        cart = Cart.objects.create(user_id=self.user.id)
        CartItem.objects.create(cart=cart, product_id=1, variant_id=2, quantity=1)

        request = self.factory.delete("/cart/remove/1/2/")
        force_authenticate(request, user=self.user)

        response = CartViewSet.as_view({"delete": "remove"})(request, product_id=1, variant_id=2)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(CartItem.objects.filter(cart=cart, product_id=1, variant_id=2).exists())

    def test_remove_returns_400_when_item_does_not_exist(self):
        Cart.objects.create(user_id=self.user.id)

        request = self.factory.delete("/cart/remove/99/99/")
        force_authenticate(request, user=self.user)

        response = CartViewSet.as_view({"delete": "remove"})(request, product_id=99, variant_id=99)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("api.views.views.get_product")
    @patch("api.views.views.get_jwt_token", return_value="mock-token")
    def test_list_returns_items_with_product_details(self, mock_jwt, mock_get_product):
        mock_get_product.return_value = {
            "name": "Cool Shoe",
            "product_variant": {"price": "49.99", "colour": "Red", "size": "medium", "type": "laptop"},
        }

        cart = Cart.objects.create(user_id=self.user.id)
        CartItem.objects.create(cart=cart, product_id=1, variant_id=2, quantity=2)

        request = self.factory.get("/cart/")
        force_authenticate(request, user=self.user)

        response = CartViewSet.as_view({"get": "list"})(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Cool Shoe - Red - medium - laptop")
        self.assertAlmostEqual(response.data[0]["price"], 49.99)

    @patch("api.views.views.get_product")
    @patch("api.views.views.get_jwt_token", return_value="mock-token")
    def test_list_creates_cart_if_not_exists(self, mock_jwt, mock_get_product):
        request = self.factory.get("/cart/")
        force_authenticate(request, user=self.user)

        response = CartViewSet.as_view({"get": "list"})(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
        self.assertTrue(Cart.objects.filter(user_id=self.user.id).exists())

    @patch("api.views.views.stripe.PaymentIntent.create")
    @patch("api.views.views.calculate_total", return_value=9999)
    @patch("api.views.views.create_order_from_items")
    @patch("api.views.views.get_jwt_token", return_value="mock-token")
    def test_checkout_creates_order_and_payment(self, mock_jwt, mock_create_order, mock_total, mock_stripe):
        from .models import Order

        mock_order = Order.objects.create(
            user_id=self.user.id,
            status=Order.OPEN,
        )

        mock_create_order.return_value = mock_order

        mock_intent = MagicMock()
        mock_intent.id = "pi_test_123"
        mock_intent.client_secret = "secret_abc"
        mock_stripe.return_value = mock_intent

        cart = Cart.objects.create(user_id=self.user.id)
        CartItem.objects.create(cart=cart, product_id=1, variant_id=2, quantity=2)

        request = self.factory.post("/cart/checkout/")
        force_authenticate(request, user=self.user)

        response = CartViewSet.as_view({"post": "checkout"})(request)
        self.assertEqual(response.status_code, 201)
        self.assertIn("client_secret", response.data)
        self.assertEqual(response.data["client_secret"], "secret_abc")

        # Cart should be deleted after checkout
        self.assertFalse(Cart.objects.filter(user_id=self.user.id).exists())

        mock_stripe.assert_called_once_with(amount=9999, currency="gbp", metadata={"order_id": 1})

    def test_checkout_returns_400_when_cart_is_empty(self):
        Cart.objects.create(user_id=self.user.id)

        request = self.factory.post("/cart/checkout/")
        force_authenticate(request, user=self.user)

        response = CartViewSet.as_view({"post": "checkout"})(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, "Cart has no items")

    @patch("api.views.views.create_order_from_items", side_effect=ValueError("Product out of stock: 1"))
    @patch("api.views.views.get_jwt_token", return_value="mock-token")
    def test_checkout_returns_409_when_product_out_of_stock(self, mock_jwt, mock_create_order):
        cart = Cart.objects.create(user_id=self.user.id)
        CartItem.objects.create(cart=cart, product_id=1, variant_id=2, quantity=1)

        request = self.factory.post("/cart/checkout/")
        force_authenticate(request, user=self.user)

        response = CartViewSet.as_view({"post": "checkout"})(request)

        self.assertEqual(response.status_code, 409)
        self.assertIn("out of stock", response.data)

    @patch("api.views.views.create_order_from_items", side_effect=Exception("Unexpected error"))
    @patch("api.views.views.get_jwt_token", return_value="mock-token")
    def test_checkout_returns_400_on_unexpected_exception(self, mock_jwt, mock_create_order):
        cart = Cart.objects.create(user_id=self.user.id)
        CartItem.objects.create(cart=cart, product_id=1, variant_id=2, quantity=1)

        request = self.factory.post("/cart/checkout/")
        force_authenticate(request, user=self.user)

        response = CartViewSet.as_view({"post": "checkout"})(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("Failed to create order", response.data)


class CreateOrderFromItemsTestCase(TestCase):
    """Unit tests for the create_order_from_items helper."""

    def setUp(self):
        self.user = User.objects.create_user(username="orderuser", password="password")
        self.order_items_data = [
            {"product_id": 1, "variant_id": 2, "quantity": 3},
        ]

    @patch("api.services.publish_message")
    @patch("api.services.bulk_reserve_order", return_value=(True, None))
    def test_creates_order_and_order_items(self, mock_reserve, mock_publish):
        from .services import create_order_from_items

        order = create_order_from_items(user=self.user, token="tok", order_items_data=self.order_items_data)

        from .models import Order, OrderItem

        self.assertIsNotNone(order.pk)
        self.assertEqual(OrderItem.objects.filter(order=order).count(), 1)

    @patch("api.services.publish_message")
    @patch("api.services.bulk_reserve_order", return_value=(False, 1))
    def test_raises_value_error_when_product_out_of_stock(self, mock_reserve, mock_publish):
        from .services import create_order_from_items

        with self.assertRaises(ValueError) as ctx:
            create_order_from_items(user=self.user, token="tok", order_items_data=self.order_items_data)

        self.assertIn("out of stock", str(ctx.exception).lower())
        mock_publish.assert_not_called()

    @patch("api.services.publish_message")
    @patch("api.services.bulk_reserve_order", return_value=(True, None))
    def test_publishes_release_and_reraises_on_db_error(self, mock_reserve, mock_publish):
        from .services import create_order_from_items
        from .models import Order

        with patch.object(Order.objects, "create", side_effect=Exception("DB down")):
            with self.assertRaises(Exception):
                create_order_from_items(user=self.user, token="tok", order_items_data=self.order_items_data)

        mock_publish.assert_called_once_with(self.order_items_data, "release-product")

    @patch("api.services.publish_message")
    @patch("api.services.bulk_reserve_order", return_value=(True, None))
    def test_publishes_send_order_email_on_success(self, mock_reserve, mock_publish):
        from .services import create_order_from_items

        create_order_from_items(user=self.user, token="tok_xyz", order_items_data=self.order_items_data)

        email_call = mock_publish.call_args
        self.assertEqual(email_call[0][1], "send-order-email")
        self.assertEqual(email_call[0][0]["token"], "tok_xyz")
        self.assertEqual(email_call[0][0]["user_id"], self.user.id)
