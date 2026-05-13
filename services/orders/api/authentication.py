import requests
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from orders import settings


class RemoteJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]

        try:
            response = requests.get(
                f"{settings.AUTH_SERVICE_URL}api/auth/verify/",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5,
            )

        except requests.exceptions.RequestException:
            raise AuthenticationFailed("Auth service unreachable")

        if response.status_code != 200:
            raise AuthenticationFailed("Invalid or expired token")

        user_data = response.json()
        return (User(user_data), token)


class User:
    def __init__(self, data):
        self.id = data.get("id")
        self.email = data.get("email")
        self.is_authenticated = True
        self.is_active = True
