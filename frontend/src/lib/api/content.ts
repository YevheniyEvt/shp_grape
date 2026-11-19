/**
 * Content API (`/api/content/`): site settings, home page, news, articles, links, pages and
 * the gallery. Server-only cached reads (`"use cache"`); admin changes appear within minutes.
 */

import { cacheLife } from "next/cache";

import type { Locale } from "@/i18n/config";
import type { components } from "@/types/api";

import { ApiError, apiFetch } from "./client";

type Schemas = components["schemas"];
export type SiteSettings = Schemas["SiteSettings"];
export type HomeContent = Schemas["Home"];
export type NewsListItem = Schemas["NewsList"];
export type NewsDetail = Schemas["NewsDetail"];
export type ArticleListItem = Schemas["ArticleList"];
export type ArticleDetail = Schemas["ArticleDetail"];
export type NewsPage = Schemas["PaginatedNewsListList"];
export type ArticlePage = Schemas["PaginatedArticleListList"];
export type UsefulLink = Schemas["UsefulLink"];
export type ContentPage = Schemas["Page"];
export type AlbumListItem = Schemas["AlbumList"];
export type AlbumDetail = Schemas["AlbumDetail"];
export type ContentPhoto = Schemas["ContentPhoto"];
export type FeedPhoto = Schemas["FeedPhoto"];
export type FeedPage = Schemas["PaginatedFeedPhotoList"];
export type Cover = Schemas["Cover"];

/** Used when the API is unreachable: the layout still renders with the built-in background. */
export const DEFAULT_SITE_SETTINGS: SiteSettings = {
  site_name: "",
  tagline: "",
  owner_name: "",
  phones: [],
  email: "",
  address: "",
  map: null,
  price_list: null,
  social: { facebook: "", instagram: "", youtube: "", telegram: "", forum: "" },
  show_background: true,
  background_image: null,
};

export const CONTENT_PAGE_SIZE = 12;

async function orNull<T>(request: Promise<T>): Promise<T | null> {
  try {
    return await request;
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

/** Site settings for the header, footer and contacts; defaults when the API is down. */
export async function getSiteSettings(locale: Locale): Promise<SiteSettings> {
  "use cache";
  cacheLife("minutes");
  try {
    return await apiFetch<SiteSettings>("/api/content/settings/", { locale });
  } catch {
    return DEFAULT_SITE_SETTINGS;
  }
}

export async function getHome(locale: Locale): Promise<HomeContent> {
  "use cache";
  cacheLife("minutes");
  return apiFetch<HomeContent>("/api/content/home/", { locale });
}

const EMPTY_PAGE = { count: 0, next: null, previous: null, results: [] };

export async function getNewsPage(locale: Locale, page: number): Promise<NewsPage> {
  "use cache";
  cacheLife("minutes");
  const result = await orNull(
    apiFetch<NewsPage>(`/api/content/news/?page=${page}&page_size=${CONTENT_PAGE_SIZE}`, {
      locale,
    }),
  );
  return result ?? EMPTY_PAGE;
}

export async function getNews(locale: Locale, slug: string): Promise<NewsDetail | null> {
  "use cache";
  cacheLife("minutes");
  return orNull(apiFetch<NewsDetail>(`/api/content/news/${encodeURIComponent(slug)}/`, { locale }));
}

export async function getArticlesPage(locale: Locale, page: number): Promise<ArticlePage> {
  "use cache";
  cacheLife("minutes");
  const result = await orNull(
    apiFetch<ArticlePage>(`/api/content/articles/?page=${page}&page_size=${CONTENT_PAGE_SIZE}`, {
      locale,
    }),
  );
  return result ?? EMPTY_PAGE;
}

export async function getArticle(locale: Locale, slug: string): Promise<ArticleDetail | null> {
  "use cache";
  cacheLife("minutes");
  return orNull(
    apiFetch<ArticleDetail>(`/api/content/articles/${encodeURIComponent(slug)}/`, { locale }),
  );
}

export async function getUsefulLinks(locale: Locale): Promise<UsefulLink[]> {
  "use cache";
  cacheLife("minutes");
  return apiFetch<UsefulLink[]>("/api/content/links/", { locale });
}

export async function getContentPage(locale: Locale, slug: string): Promise<ContentPage | null> {
  "use cache";
  cacheLife("minutes");
  return orNull(
    apiFetch<ContentPage>(`/api/content/pages/${encodeURIComponent(slug)}/`, { locale }),
  );
}

export async function getAlbums(locale: Locale): Promise<AlbumListItem[]> {
  "use cache";
  cacheLife("minutes");
  return apiFetch<AlbumListItem[]>("/api/content/gallery/albums/", { locale });
}

export async function getAlbum(locale: Locale, slug: string): Promise<AlbumDetail | null> {
  "use cache";
  cacheLife("minutes");
  return orNull(
    apiFetch<AlbumDetail>(`/api/content/gallery/albums/${encodeURIComponent(slug)}/`, {
      locale,
    }),
  );
}

/** First page of the photo feed; next pages are loaded in the browser. */
export async function getPhotoFeed(locale: Locale): Promise<FeedPage> {
  "use cache";
  cacheLife("minutes");
  return apiFetch<FeedPage>("/api/content/gallery/photos/?page=1", { locale });
}
