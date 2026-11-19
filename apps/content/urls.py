from django.urls import path

from apps.content import views

app_name = "content"

urlpatterns = [
    path("settings/", views.SiteSettingsView.as_view(), name="site-settings"),
    path("home/", views.HomeView.as_view(), name="home"),
    path("news/", views.NewsListView.as_view(), name="news-list"),
    path("news/<slug:slug>/", views.NewsDetailView.as_view(), name="news-detail"),
    path("articles/", views.ArticleListView.as_view(), name="article-list"),
    path("articles/<slug:slug>/", views.ArticleDetailView.as_view(), name="article-detail"),
    path("links/", views.UsefulLinkListView.as_view(), name="link-list"),
    path("pages/<slug:slug>/", views.PageDetailView.as_view(), name="page-detail"),
    path("gallery/albums/", views.AlbumListView.as_view(), name="album-list"),
    path("gallery/albums/<slug:slug>/", views.AlbumDetailView.as_view(), name="album-detail"),
    path("gallery/photos/", views.PhotoFeedView.as_view(), name="photo-feed"),
]
