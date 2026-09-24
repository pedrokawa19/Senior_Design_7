"""Root URL routing: the Django admin plus everything the dashboard app owns."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("dashboard.urls")),
]
