import { CalendarIcon, ChevronRightIcon, UserIcon } from "lucide-react";
import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";

import { Pagination } from "@/components/common/pagination";
import { RichText } from "@/components/common/rich-text";
import { PhotoAlbum } from "@/components/media/photo-album";
import { YouTubeVideos } from "@/components/media/youtube-videos";
import { localizePath, type Locale } from "@/i18n/config";
import { getTranslator } from "@/i18n/server";
import {
  type ArticleDetail,
  CONTENT_PAGE_SIZE,
  getArticle,
  getArticlesPage,
  getNews,
  getNewsPage,
  type NewsDetail,
} from "@/lib/api/content";
import { formatDate, pageNumber, plainText } from "@/lib/format";

import { PublicationCard } from "./publication-card";

export type PublicationKind = "news" | "articles";

const fetchers = {
  news: { page: getNewsPage, item: getNews },
  articles: { page: getArticlesPage, item: getArticle },
};

/** A page of news or articles with pagination; reads `?page=`, so render it in `<Suspense>`. */
export async function PublicationList({
  kind,
  searchParams,
}: {
  kind: PublicationKind;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { t, locale } = await getTranslator();
  const page = pageNumber((await searchParams).page);
  const data = await fetchers[kind].page(locale, page);
  const basePath = localizePath(`/${kind}`, locale);

  if (!data.results.length) {
    return <p className="text-muted-foreground">{t("Nothing has been published yet.")}</p>;
  }
  return (
    <div className="grid gap-8">
      <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {data.results.map((item) => (
          <li key={item.id}>
            <PublicationCard item={item} href={`${basePath}/${item.slug}`} locale={locale} />
          </li>
        ))}
      </ul>
      <Pagination
        page={page}
        totalPages={Math.ceil(data.count / CONTENT_PAGE_SIZE)}
        hrefFor={(number) => (number > 1 ? `${basePath}?page=${number}` : basePath)}
        t={t}
      />
    </div>
  );
}

async function loadPublication(kind: PublicationKind, slug: string, locale: Locale) {
  const item = await fetchers[kind].item(locale, slug);
  if (!item) notFound();
  return item as NewsDetail & Partial<ArticleDetail>;
}

export async function publicationMetadata(
  kind: PublicationKind,
  params: Promise<{ slug: string }>,
): Promise<Metadata> {
  const { slug } = await params;
  const { locale } = await getTranslator();
  const item = await loadPublication(kind, slug, locale);
  const description = item.excerpt || plainText(item.body, 160);
  return {
    title: item.title,
    description,
    openGraph: {
      type: "article",
      title: item.title,
      description,
      publishedTime: item.published_at,
      ...(item.cover && { images: [{ url: item.cover.large }] }),
    },
  };
}

/** A news item or an article; reads the slug, so render it in `<Suspense>`. */
export async function PublicationView({
  kind,
  params,
}: {
  kind: PublicationKind;
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const { t, locale } = await getTranslator();
  const item = await loadPublication(kind, slug, locale);
  const href = (path: string) => localizePath(path, locale);
  const section = kind === "news" ? t("News") : t("Articles");

  return (
    <article className="mx-auto grid max-w-3xl gap-8">
      <nav aria-label={t("Breadcrumbs")}>
        <ol className="flex flex-wrap items-center gap-1 text-sm text-muted-foreground">
          <li>
            <Link href={href("/")} className="hover:text-primary">
              {t("Home")}
            </Link>
          </li>
          <ChevronRightIcon className="size-4" aria-hidden="true" />
          <li>
            <Link href={href(`/${kind}`)} className="hover:text-primary">
              {section}
            </Link>
          </li>
        </ol>
      </nav>

      <header className="grid gap-3">
        <h1 className="text-3xl leading-tight font-semibold sm:text-4xl">{item.title}</h1>
        <p className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <CalendarIcon className="size-4" aria-hidden="true" />
            <time dateTime={item.published_at}>{formatDate(item.published_at ?? "", locale)}</time>
          </span>
          {item.author && (
            <span className="flex items-center gap-1.5">
              <UserIcon className="size-4" aria-hidden="true" />
              {item.author}
            </span>
          )}
        </p>
      </header>

      {item.cover && (
        <Image
          src={item.cover.large}
          alt=""
          width={item.cover.width ?? 1600}
          height={item.cover.height ?? 900}
          sizes="(min-width: 768px) 768px, 100vw"
          preload
          unoptimized
          className="w-full rounded-xl object-cover"
        />
      )}

      <RichText html={item.body ?? ""} />

      {item.photos && item.photos.length > 0 && (
        <section aria-labelledby="photos" className="grid gap-3">
          <h2 id="photos" className="text-xl font-semibold">
            {t("Photos")}
          </h2>
          <PhotoAlbum images={item.photos} />
        </section>
      )}

      {item.videos && item.videos.length > 0 && (
        <section aria-labelledby="videos" className="grid gap-3">
          <h2 id="videos" className="text-xl font-semibold">
            {t("Videos")}
          </h2>
          <YouTubeVideos videos={item.videos} fallbackTitle={item.title} />
        </section>
      )}
    </article>
  );
}
