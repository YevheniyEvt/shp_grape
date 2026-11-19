import { ChevronLeftIcon } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { PhotoAlbum } from "@/components/media/photo-album";
import { Skeleton } from "@/components/ui/skeleton";
import { localizePath } from "@/i18n/config";
import { getTranslator } from "@/i18n/server";
import { getAlbum } from "@/lib/api/content";

export async function generateMetadata({
  params,
}: PageProps<"/[lang]/gallery/[slug]">): Promise<Metadata> {
  const { slug } = await params;
  const { locale } = await getTranslator();
  const album = await getAlbum(locale, slug);
  if (!album) notFound();
  return {
    title: album.title,
    description: album.description || undefined,
    ...(album.cover && { openGraph: { images: [{ url: album.cover.large }] } }),
  };
}

async function Album({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const { t, locale } = await getTranslator();
  const album = await getAlbum(locale, slug);
  if (!album) notFound();

  return (
    <>
      <Link
        href={localizePath("/gallery", locale)}
        className="mb-4 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-primary"
      >
        <ChevronLeftIcon className="size-4" aria-hidden="true" />
        {t("All albums")}
      </Link>
      <h1 className="mb-2 text-3xl font-semibold sm:text-4xl">{album.title}</h1>
      {album.description && (
        <p className="mb-6 max-w-3xl text-muted-foreground">{album.description}</p>
      )}
      <PhotoAlbum images={album.photos} />
    </>
  );
}

export default function AlbumPage({ params }: PageProps<"/[lang]/gallery/[slug]">) {
  return (
    <div className="mx-auto max-w-7xl px-4 py-10">
      <Suspense fallback={<Skeleton className="h-96 w-full rounded-xl" />}>
        <Album params={params} />
      </Suspense>
    </div>
  );
}
