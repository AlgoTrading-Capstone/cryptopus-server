from django.urls import path
from apps.agent.views import (
    ActiveAgentView,
    ActiveAgentMetricsView,
    ActiveAgentPlotsView,
    ActiveAgentExplanationView,
    AgentStatusView,
)

urlpatterns = [
    path("active", ActiveAgentView.as_view()),
    path("active/metrics", ActiveAgentMetricsView.as_view()),
    path("active/plots", ActiveAgentPlotsView.as_view()),
    path("active/explanation", ActiveAgentExplanationView.as_view()),
    path("status", AgentStatusView.as_view()),
]