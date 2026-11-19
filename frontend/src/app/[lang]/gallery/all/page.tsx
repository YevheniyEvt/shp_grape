import type { Metadata } from "next";

import { GalleryTabs } from "@/components/content/gallery-tabs";
import { PhotoFeed } from "@/components/content/photo-feed";
import { localizePath } from "@/i18n/config";
import { getTranslator } from "@/i18n/server";
import { getPhotoFeed } from "@/lib/api/content";

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getTranslator();
  return { title: t("All photos"), description: t("Photos of our vineyard and grape varieties.") };
}

export default async function AllPhotosPage() {
  const { t, locale } = await getTranslator();
  const feed = await getPhotoFeed(locale);

  return (
    <div className="mx-auto max-w-7xl px-4 py-10">
      <h1 className="mb-6 text-3xl font-semibold sm:text-4xl">{t("Gallery")}</h1>
      <GalleryTabs active="all" hrefFor={(path) => localizePath(path, locale)} t={t} />
      {feed.results.length ? (
        <PhotoFeed initial={feed.results} hasMore={feed.next_page !== null} />
      ) : (
        <p className="text-muted-foreground">{t("Nothing has been published yet.")}</p>
      )}
    </div>
  );
}
