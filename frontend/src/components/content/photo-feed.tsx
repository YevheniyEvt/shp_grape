"use client";

import { LoaderCircleIcon } from "lucide-react";

import { type GalleryImage, InfinitePhotoAlbum } from "@/components/media/photo-album";
import { useT } from "@/i18n/client";
import type { FeedPhoto } from "@/lib/api/content";
import { fetchPhotoFeedPage } from "@/lib/api/views";

export function feedImage(photo: FeedPhoto): GalleryImage {
  return { ...photo, alt: photo.alt || photo.source.title };
}

/** All photos of albums and varieties; more pages load while scrolling. */
export function PhotoFeed({ initial, hasMore }: { initial: FeedPhoto[]; hasMore: boolean }) {
  const { t, locale } = useT();
  return (
    <InfinitePhotoAlbum
      initial={initial.map(feedImage)}
      hasMore={hasMore}
      loadPage={async (page) => {
        const data = await fetchPhotoFeedPage(page, locale);
        return { images: data.results.map(feedImage), hasMore: data.next_page !== null };
      }}
      loading={
        <p className="flex justify-center py-6 text-muted-foreground" role="status">
          <LoaderCircleIcon className="size-5 animate-spin" aria-hidden="true" />
          <span className="sr-only">{t("Loading…")}</span>
        </p>
      }
      finished={
        <p className="py-6 text-center text-sm text-muted-foreground">
          {t("You have seen all the photos.")}
        </p>
      }
    />
  );
}
