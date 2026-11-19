"""factory-boy factories of the content app."""

import factory
from factory.django import DjangoModelFactory, ImageField

from apps.content.models import (
    Article,
    ArticlePhoto,
    ArticleVideo,
    GalleryAlbum,
    GalleryPhoto,
    News,
    Page,
    UsefulLink,
)


class NewsFactory(DjangoModelFactory):
    title_uk = factory.Sequence(lambda n: f"Новина {n}")
    title_en = factory.Sequence(lambda n: f"News {n}")
    body_uk = "<p>Текст новини</p>"

    class Meta:
        model = News


class ArticleFactory(DjangoModelFactory):
    title_uk = factory.Sequence(lambda n: f"Стаття {n}")
    title_en = factory.Sequence(lambda n: f"Article {n}")
    excerpt_uk = "Короткий опис"
    body_uk = "<p>Текст статті</p>"

    class Meta:
        model = Article


class ArticlePhotoFactory(DjangoModelFactory):
    article = factory.SubFactory(ArticleFactory)
    image = ImageField(width=40, height=30, color="green", format="JPEG")
    order = factory.Sequence(lambda n: n)

    class Meta:
        model = ArticlePhoto


class ArticleVideoFactory(DjangoModelFactory):
    article = factory.SubFactory(ArticleFactory)
    youtube_url = "https://youtu.be/dQw4w9WgXcQ"

    class Meta:
        model = ArticleVideo


class UsefulLinkFactory(DjangoModelFactory):
    title_uk = factory.Sequence(lambda n: f"Посилання {n}")
    url = factory.Sequence(lambda n: f"https://example.com/{n}")
    order = factory.Sequence(lambda n: n)

    class Meta:
        model = UsefulLink


class PageFactory(DjangoModelFactory):
    title_uk = factory.Sequence(lambda n: f"Сторінка {n}")
    body_uk = "<p>Текст</p>"

    class Meta:
        model = Page


class GalleryAlbumFactory(DjangoModelFactory):
    title_uk = factory.Sequence(lambda n: f"Альбом {n}")
    title_en = factory.Sequence(lambda n: f"Album {n}")
    order = factory.Sequence(lambda n: n)

    class Meta:
        model = GalleryAlbum


class GalleryPhotoFactory(DjangoModelFactory):
    album = factory.SubFactory(GalleryAlbumFactory)
    image = ImageField(width=40, height=30, color="purple", format="JPEG")
    order = factory.Sequence(lambda n: n)

    class Meta:
        model = GalleryPhoto
