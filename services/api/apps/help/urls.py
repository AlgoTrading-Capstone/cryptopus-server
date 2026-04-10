from django.urls import path
from apps.help.views import (
    HelpOverviewView,
    HelpStrategiesView,
    HelpRiskManagementView,
    HelpFaqView,
)

urlpatterns = [
    path("overview", HelpOverviewView.as_view()),
    path("strategies", HelpStrategiesView.as_view()),
    path("risk-management", HelpRiskManagementView.as_view()),
    path("faq", HelpFaqView.as_view()),
]