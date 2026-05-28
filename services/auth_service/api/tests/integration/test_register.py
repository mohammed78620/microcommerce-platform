from unittest.mock import patch

from rest_framework.response import Response
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIRequestFactory
from api.views import RegisterView

User = get_user_model()


class RegisterViewTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = RegisterView.as_view()
        self.valid_user_input = {
            "email": "user@gmail.com",
            "password": "password1wefwefer3425fdas:23!",
            "username": "user1",
        }
        self.invalid_user_input = {
            "email": "user@gmail.com",
            "password": "password",
            "username": "user1",
        }

    def _make_request(self, data):
        request = self.factory.post("/register/", data, format="json")
        return request

    @patch("api.views.send_verification_email")
    def test_user_registered(self, mock_send_verification_email):
        mock_send_verification_email.return_value = Response({"message": "Email sent."}, status=200)
        request = self._make_request(self.valid_user_input)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "Successfully registered user.")

    @patch("api.views.send_verification_email")
    def test_user_already_registered(self, mock_send_verification_email):
        mock_send_verification_email.return_value = Response({"message": "Email sent."}, status=200)
        User.objects.create_user(
            username=self.valid_user_input["username"],
            email=self.valid_user_input["email"],
            password=self.valid_user_input["password"],
        )

        request = self._make_request(self.valid_user_input)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data["email"][0]), "Email already registered.")

    @patch("api.views.send_verification_email")
    def test_invalid_password(self, mock_send_verification_email):
        mock_send_verification_email.return_value = Response({"message": "Email sent."}, status=200)
        request = self._make_request(self.invalid_user_input)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data["password"][0]), "This password is too common.")
