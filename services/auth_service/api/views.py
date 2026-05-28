from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.forms.models import model_to_dict
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core import signing
from django.views import View
from django.contrib.auth import authenticate
import requests
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password


from auth_service.settings import EMAILS_SERVICE_URL
import common.utils.token as token_utils


def send_verification_email(payload):
    response = requests.post(f"{EMAILS_SERVICE_URL}api/send_verification_email/", json=payload)
    return response


class UserAPIView(APIView):
    def get(self, request, pk):
        user = User.objects.get(pk=pk)
        if user:

            return Response(model_to_dict(user), status.HTTP_200_OK)
        else:
            return Response({"message": "No users available"}, status=status.HTTP_404_NOT_FOUND)


# Add this view
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def verify_token(request):
    user = request.user
    return Response({"id": user.id, "email": user.email})


class CustomTokenObtainPairView(TokenObtainPairView):

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)

        if user:
            response.data["user"] = {
                "id": user.id,
                "username": user.username,
                "email": getattr(user, "email", ""),
            }

        return response


class RegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    username = serializers.CharField(max_length=150)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value


class RegisterView(APIView):
    def post(self, request, *args, **kwargs):
        # validate input data
        serializer = RegistrationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # create user token
        user = User.objects.create_user(
            username=serializer.validated_data["username"],
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            is_active=False,  # locked until email verified
        )
        token = token_utils.generate_verification_token(user.id)

        # send verification email
        try:
            response = send_verification_email({"token": token, "email": user.email})
        except requests.RequestException as e:
            user.delete()
            return Response({"error": "Email service unavailable."}, status=502)

        if response.status_code != 200:
            return Response(response.text, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Successfully registered user."}, status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
    def get(self, request):
        token = request.query_params.get("token")
        try:
            user_id = token_utils.verify_token(token)
        except signing.SignatureExpired:
            return Response({"error": "Token expired."}, status=400)
        except signing.BadSignature:
            return Response({"error": "Invalid token."}, status=400)

        User.objects.filter(id=user_id).update(is_active=True)
        return Response({"message": "Email verified. You can now log in."})
