from django.urls import path
from apps.system.views import HealthView, VersionView

urlpatterns = [
    path("health", HealthView.as_view()),
    path("version", VersionView.as_view()),
]