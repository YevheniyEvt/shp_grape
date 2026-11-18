from django.urls import path

from apps.catalog import views

app_name = "catalog"

urlpatterns = [
    path("varieties/", views.VarietyListView.as_view(), name="variety-list"),
    path("varieties/<slug:slug>/", views.VarietyDetailView.as_view(), name="variety-detail"),
    path(
        "varieties/<slug:slug>/view/",
        views.VarietyViewCountView.as_view(),
        name="variety-view",
    ),
    path("filters/", views.FilterOptionsView.as_view(), name="filters"),
    path("letters/", views.LettersView.as_view(), name="letters"),
    path("photos/random/", views.RandomPhotosView.as_view(), name="random-photos"),
]
