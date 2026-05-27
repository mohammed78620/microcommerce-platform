from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.core.mail import send_mail

from emails.settings import AUTH_SERVICE_URL, DEFAULT_FROM_EMAIL


class SendVerificationView(APIView):
    def post(self, request):
        email = request.data.get("email")
        token = request.data.get("token")

        if not email or not token:
            return Response({"error": "Missing fields."}, status=400)

        verification_link = f"{AUTH_SERVICE_URL}api/verify_email/?token={token}"
        print(verification_link)

        send_mail(
            subject="Verify your email",
            message=f"Click to verify: {verification_link}",
            from_email=DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        return Response({"message": "Email sent."}, status=200)
