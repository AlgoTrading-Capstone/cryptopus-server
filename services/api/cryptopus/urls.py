"""
URL configuration for cryptopus project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("api/auth/", include("apps.authentication.urls")),
    path("api/exchange/", include("apps.exchange.urls")),
    path("api/trading/", include("apps.trading.urls")),
    path("api/portfolio/", include("apps.portfolio.urls")),
    path("api/agent/", include("apps.agent.urls")),
    path("api/admin/", include("apps.admin_panel.urls")),
    path("api/alerts/", include("apps.alerts.urls")),
    path("api/help/", include("apps.help.urls")),
]
