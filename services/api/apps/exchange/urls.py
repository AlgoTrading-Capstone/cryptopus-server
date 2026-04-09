from django.urls import path
from apps.exchange.views import (
    KrakenOnboardingView,
    KrakenConnectView,
    KrakenStatusView,
    KrakenValidateView,
    KrakenDisconnectView,
)

urlpatterns = [
    path("kraken/onboarding", KrakenOnboardingView.as_view()),
    path("kraken/connect", KrakenConnectView.as_view()),
    path("kraken/status", KrakenStatusView.as_view()),
    path("kraken/validate", KrakenValidateView.as_view()),
    path("kraken/disconnect", KrakenDisconnectView.as_view()),
]