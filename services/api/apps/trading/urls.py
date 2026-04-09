from django.urls import path
from apps.trading.views import (
    AllocateView,
    WithdrawView,
    ToggleView,
    TradingStatusView,
)

urlpatterns = [
    path("allocate", AllocateView.as_view()),
    path("withdraw", WithdrawView.as_view()),
    path("toggle", ToggleView.as_view()),
    path("status", TradingStatusView.as_view()),
]