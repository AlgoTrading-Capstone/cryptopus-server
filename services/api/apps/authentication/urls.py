from django.urls import path
from apps.authentication.views import RegisterView, VerifyEmailView, SetupOtpView, VerifyOtpSetupView

urlpatterns = [
    path("register", RegisterView.as_view()),
    path("verify-email", VerifyEmailView.as_view()),
    path("setup-otp", SetupOtpView.as_view()),
    path("verify-otp-setup", VerifyOtpSetupView.as_view()),
]