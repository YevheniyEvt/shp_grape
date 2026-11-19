from django.urls import path

from apps.content import views

app_name = "content"

urlpatterns = [
    path("settings/", views.SiteSettingsView.as_view(), name="site-settings"),
]
