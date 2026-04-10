from django.urls import path
from apps.alerts.views import (
    AlertsView,
    AlertMarkReadView,
    AlertPreferencesView,
)

urlpatterns = [
    path("", AlertsView.as_view()),
    path("<uuid:alert_id>/read", AlertMarkReadView.as_view()),
    path("preferences", AlertPreferencesView.as_view()),
]