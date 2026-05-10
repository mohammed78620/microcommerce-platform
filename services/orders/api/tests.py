from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from api.models import Order, OrderItem
from services.orders.api.views.views import OrderViewSet

User = get_user_model()


class OrderViewSetListTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.view = OrderViewSet.as_view({"get": "list"})

    def test_list_returns_orders_with_items(self):
        order = Order.objects.create(user_id=self.user.id)
        OrderItem.objects.create(order=order, product_id=1, quantity=2)

        request = self.factory.get("/orders/")
        force_authenticate(request, user=self.user)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertIn("order_items", response.data[0])
        self.assertEqual(len(response.data[0]["order_items"]), 1)

    def test_list_returns_empty_when_no_orders(self):
        request = self.factory.get("/orders/")
        force_authenticate(request, user=self.user)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])


class OrderViewSetCreateTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.view = OrderViewSet.as_view({"post": "create"})
        self.valid_payload = {
            "order_items": [
                {"product_id": 1, "quantity": 2},
                {"product_id": 2, "quantity": 1},
            ]
        }

    def _make_request(self, data):
        request = self.factory.post("/orders/", data, format="json")
        force_authenticate(request, user=self.user)
        return request

    # ------------------------------------------------------------------
    # Validation tests
    # ------------------------------------------------------------------

    def test_create_returns_400_when_no_order_data(self):
        request = self._make_request({})
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_returns_400_when_order_items_missing(self):
        request = self._make_request({"some_field": "value"})
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_returns_400_when_order_items_empty_list(self):
        request = self._make_request({"order_items": []})
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ------------------------------------------------------------------
    # Product reservation tests
    # ------------------------------------------------------------------

    @patch("api.views.get_jwt_token", return_value="mock-jwt-token")
    @patch("api.views.bulk_reserve_order", return_value=(False, 42))
    def test_create_raises_when_product_out_of_stock(self, mock_reserve, mock_jwt):
        request = self._make_request(self.valid_payload)

        with self.assertRaises(ValueError) as ctx:
            self.view(request)

        self.assertIn("42", str(ctx.exception))
        mock_reserve.assert_called_once_with(
            "mock-jwt-token",
            [{"product_id": 1, "quantity": 2}, {"product_id": 2, "quantity": 1}],
        )

    # ------------------------------------------------------------------
    # Happy path
    # ------------------------------------------------------------------

    @patch("api.views.get_jwt_token", return_value="mock-jwt-token")
    @patch("api.views.bulk_reserve_order", return_value=(True, None))
    @patch("api.views.publish_message")
    def test_create_order_success(self, mock_publish, mock_reserve, mock_jwt):
        request = self._make_request(self.valid_payload)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Order and items persisted
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 2)

        # Email message published exactly once with correct topic
        mock_publish.assert_called_once()
        call_args = mock_publish.call_args
        self.assertEqual(call_args[0][1], "send-order-email")

        email_payload = call_args[0][0]
        self.assertEqual(email_payload["user_id"], self.user.id)
        self.assertEqual(email_payload["token"], "mock-jwt-token")

    @patch("api.views.get_jwt_token", return_value="mock-jwt-token")
    @patch("api.views.bulk_reserve_order", return_value=(True, None))
    @patch("api.views.publish_message")
    def test_create_uses_authenticated_user_id(self, mock_publish, mock_reserve, mock_jwt):
        request = self._make_request(self.valid_payload)
        self.view(request)

        order = Order.objects.get()
        self.assertEqual(order.user_id, self.user.id)

    # ------------------------------------------------------------------
    # Failure / rollback tests
    # ------------------------------------------------------------------

    @patch("api.views.get_jwt_token", return_value="mock-jwt-token")
    @patch("api.views.bulk_reserve_order", return_value=(True, None))
    @patch("api.views.publish_message")
    @patch("api.models.OrderItem.objects.bulk_create", side_effect=Exception("DB error"))
    def test_create_publishes_release_message_on_db_failure(
        self, mock_bulk_create, mock_publish, mock_reserve, mock_jwt
    ):
        request = self._make_request(self.valid_payload)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # release-product message must be sent; no email message
        mock_publish.assert_called_once()
        call_args = mock_publish.call_args
        self.assertEqual(call_args[0][1], "release-product")

    @patch("api.views.get_jwt_token", return_value="mock-jwt-token")
    @patch("api.views.bulk_reserve_order", return_value=(True, None))
    @patch("api.views.publish_message")
    @patch("api.models.OrderItem.objects.bulk_create", side_effect=Exception("DB error"))
    def test_create_rolls_back_order_on_db_failure(self, mock_bulk_create, mock_publish, mock_reserve, mock_jwt):
        request = self._make_request(self.valid_payload)
        self.view(request)

        # Transaction rolled back — no order should remain
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)

    # ------------------------------------------------------------------
    # JWT token forwarding
    # ------------------------------------------------------------------

    @patch("api.views.get_jwt_token", return_value="bearer-xyz")
    @patch("api.views.bulk_reserve_order", return_value=(True, None))
    @patch("api.views.publish_message")
    def test_create_forwards_jwt_to_reserve_and_email(self, mock_publish, mock_reserve, mock_jwt):
        request = self._make_request(self.valid_payload)
        self.view(request)

        # Token forwarded to product service
        reserve_call_token = mock_reserve.call_args[0][0]
        self.assertEqual(reserve_call_token, "bearer-xyz")

        # Token included in email payload
        email_payload = mock_publish.call_args[0][0]
        self.assertEqual(email_payload["token"], "bearer-xyz")


class OrderViewSetCancelTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.order = Order.objects.create(user_id=self.user.id)
        self.view = OrderViewSet.as_view({"post": "cancel"})
        self.valid_payload = {
            "order_items": [
                {"product_id": 1, "quantity": 2},
                {"product_id": 2, "quantity": 1},
            ]
        }

    def _make_request(self, data, pk):
        request = self.factory.post(f"/orders/{pk}/cancel", data, format="json")
        force_authenticate(request, user=self.user)
        return request

    def test_cancel_success(self):
        request = self._make_request(self.valid_payload, self.order.pk)
        response = self.view(request, self.order.pk)
        self.assertEqual(response.status_code, 200)

    def test_cancel_fail(self):
        request = self._make_request(self.valid_payload, self.order.pk)
        response = self.view(request, 100000)
        self.assertEqual(response.status_code, 404)
