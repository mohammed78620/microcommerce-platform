from django.urls import path

from api.views import SendVerificationView

urlpatterns = [path("send_verification_email/", SendVerificationView.as_view())]
