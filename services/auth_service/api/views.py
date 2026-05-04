from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.forms.models import model_to_dict


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
