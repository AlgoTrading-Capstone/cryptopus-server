from django.urls import path
from apps.portfolio.views import (
    PortfolioSummaryView,
    PortfolioTradesView,
    PortfolioPerformanceView,
    PortfolioEquityHistoryView,
    PortfolioAllocationsView,
)

urlpatterns = [
    path("summary", PortfolioSummaryView.as_view()),
    path("trades", PortfolioTradesView.as_view()),
    path("performance", PortfolioPerformanceView.as_view()),
    path("equity-history", PortfolioEquityHistoryView.as_view()),
    path("allocations", PortfolioAllocationsView.as_view()),
]