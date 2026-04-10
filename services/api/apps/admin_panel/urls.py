from django.urls import path
from apps.admin_panel.views import (
    AdminAgentUploadView,
    AdminAgentsListView,
    AdminAgentDetailView,
    AdminAgentActivateView,
    AdminAgentDeactivateView,
    AdminHotSwapView,
    AdminSystemStatsView,
    AdminSystemHealthView,
    AdminUsersListView,
    AdminUserDetailView,
    AdminUserStatusView,
)

urlpatterns = [
    path("agents/upload", AdminAgentUploadView.as_view()),
    path("agents/hot-swap", AdminHotSwapView.as_view()),
    path("agents", AdminAgentsListView.as_view()),
    path("agents/<uuid:agent_id>", AdminAgentDetailView.as_view()),
    path("agents/<uuid:agent_id>/activate", AdminAgentActivateView.as_view()),
    path("agents/<uuid:agent_id>/deactivate", AdminAgentDeactivateView.as_view()),
    path("system/stats", AdminSystemStatsView.as_view()),
    path("system/health", AdminSystemHealthView.as_view()),
    path("users", AdminUsersListView.as_view()),
    path("users/<uuid:user_id>", AdminUserDetailView.as_view()),
    path("users/<uuid:user_id>/status", AdminUserStatusView.as_view()),
]