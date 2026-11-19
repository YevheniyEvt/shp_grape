import { ImagesIcon } from "lucide-react";
import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";

import { GalleryTabs } from "@/components/content/gallery-tabs";
import { localizePath } from "@/i18n/config";
import { getTranslator } from "@/i18n/server";
import { getAlbums } from "@/lib/api/content";
import { formatDate } from "@/lib/format";

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getTranslator();
  return { title: t("Gallery"), description: t("Photos of our vineyard and grape varieties.") };
}

export default async function GalleryPage() {
  const { t, nt, locale } = await getTranslator();
  const albums = await getAlbums(locale);
  const href = (path: string) => localizePath(path, locale);

  return (
    <div className="mx-auto max-w-7xl px-4 py-10">
      <h1 className="mb-6 text-3xl font-semibold sm:text-4xl">{t("Gallery")}</h1>
      <GalleryTabs active="albums" hrefFor={href} t={t} />
      {albums.length ? (
        <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {albums.map((album) => (
            <li key={album.id}>
              <article className="group relative overflow-hidden rounded-xl bg-card ring-1 ring-foreground/10 transition-shadow hover:shadow-lg">
                <div className="aspect-4/3 overflow-hidden bg-muted">
                  {album.cover && (
                    <Image
                      src={album.cover.medium}
                      alt={album.cover.alt}
                      width={album.cover.width ?? 1000}
                      height={album.cover.height ?? 750}
                      sizes="(min-width: 1024px) 33vw, (min-width: 640px) 50vw, 100vw"
                      unoptimized
                      className="size-full object-cover transition-transform duration-500 group-hover:scale-105"
                    />
                  )}
                </div>
                <div className="grid gap-1 p-4">
                  <h2 className="font-heading text-lg font-semibold">
                    <Link
                      href={href(`/gallery/${album.slug}`)}
                      className="after:absolute after:inset-0 hover:text-primary"
                    >
                      {album.title}
                    </Link>
                  </h2>
                  <p className="flex flex-wrap items-center gap-1.5 text-sm text-muted-foreground">
                    <ImagesIcon className="size-4" aria-hidden="true" />
                    {nt("%(count)s photo", "%(count)s photos", album.photo_count, {
                      count: album.photo_count,
                    })}
                    {album.date && <span>· {formatDate(album.date, locale)}</span>}
                  </p>
                </div>
              </article>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-muted-foreground">{t("Nothing has been published yet.")}</p>
      )}
    </div>
  );
}
