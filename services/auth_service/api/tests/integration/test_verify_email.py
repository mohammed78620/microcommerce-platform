from unittest.mock import patch

from rest_framework.response import Response
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIRequestFactory

from api.views import VerifyEmailView
from common.utils.token import generate_verification_token

User = get_user_model()


class RegisterViewTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = VerifyEmailView.as_view()
        self.user_input = {
            "email": "user@gmail.com",
            "password": "password1wefwefer3425fdas:23!",
            "username": "user1",
        }
        self.valid_token = {
            "email": "user@gmail.com",
            "password": "password1wefwefer3425fdas:23!",
            "username": "user1",
        }
        self.invalid_token = {
            "email": "user@gmail.com",
            "password": "password",
            "username": "user1",
        }

    def _make_request(self, token):
        request = self.factory.get("/verify_email/", data={"token": token})
        return request

    def test_valid_token(self):
        user = User.objects.create_user(**self.user_input)
        token = generate_verification_token(user.id)
        request = self._make_request(token)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Email verified. You can now log in.")

    def test_invalid_token(self):
        token = "invalid_token"
        request = self._make_request(token)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Invalid token.")
