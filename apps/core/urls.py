from django.urls import path

from apps.core import views

app_name = "core"

urlpatterns = [
    path("health/", views.HealthView.as_view(), name="health"),
    path("i18n/languages/", views.LanguagesView.as_view(), name="languages"),
    path("i18n/<str:lang>/", views.TranslationCatalogView.as_view(), name="translation-catalog"),
]
