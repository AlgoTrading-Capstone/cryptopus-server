from django.urls import path
from apps.authentication.views import RegisterView, VerifyEmailView

urlpatterns = [
    path("register", RegisterView.as_view()),
    path("verify-email", VerifyEmailView.as_view()),
]