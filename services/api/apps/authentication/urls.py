from django.urls import path
from apps.authentication.views import RegisterView, VerifyEmailView, SetupOtpView, VerifyOtpSetupView, LoginView, VerifyOtpView, RefreshTokenView, LogoutView

urlpatterns = [
    path("register", RegisterView.as_view()),
    path("verify-email", VerifyEmailView.as_view()),
    path("setup-otp", SetupOtpView.as_view()),
    path("verify-otp-setup", VerifyOtpSetupView.as_view()),
    path("login", LoginView.as_view()),
    path("verify-otp", VerifyOtpView.as_view()),
    path("refresh", RefreshTokenView.as_view()),
    path("logout", LogoutView.as_view()),
]