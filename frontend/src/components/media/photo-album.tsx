"use client";

import { useRef, useState } from "react";
import { type Photo as AlbumPhoto, RowsPhotoAlbum } from "react-photo-album";
import "react-photo-album/rows.css";
import InfiniteScroll from "react-photo-album/scroll";
import Lightbox from "yet-another-react-lightbox";
import Counter from "yet-another-react-lightbox/plugins/counter";
import Fullscreen from "yet-another-react-lightbox/plugins/fullscreen";
import Zoom from "yet-another-react-lightbox/plugins/zoom";
import "yet-another-react-lightbox/styles.css";
import "yet-another-react-lightbox/plugins/counter.css";

import { useT } from "@/i18n/client";

/** A photo with the three imagekit renditions the API serves. */
export type GalleryImage = {
  id: number | string;
  alt: string;
  width: number | null;
  height: number | null;
  thumb: string;
  medium: string;
  large: string;
};

const RENDITIONS = [
  ["thumb", 400],
  ["medium", 1000],
  ["large", 1800],
] as const;
const FALLBACK = { width: 1200, height: 900 };

/** Size of a rendition that fits the original into `max`×`max` without upscaling. */
export function fitSize(width: number, height: number, max: number) {
  const scale = Math.min(1, max / Math.max(width, height));
  return { width: Math.round(width * scale), height: Math.round(height * scale) };
}

type SlidePhoto = AlbumPhoto & { large: string; index: number };

/** Photo-album item with a `srcset` of all renditions, so the browser picks the right size. */
export function toAlbumPhoto(image: GalleryImage, index: number): SlidePhoto {
  const width = image.width ?? FALLBACK.width;
  const height = image.height ?? FALLBACK.height;
  return {
    key: String(image.id),
    src: image.medium,
    alt: image.alt,
    width,
    height,
    srcSet: RENDITIONS.map(([name, max]) => ({ src: image[name], ...fitSize(width, height, max) })),
    large: image.large,
    index,
  };
}

function useLightboxLabels() {
  const { t } = useT();
  return {
    Previous: t("Previous"),
    Next: t("Next"),
    Close: t("Close"),
    "Zoom in": t("Zoom in"),
    "Zoom out": t("Zoom out"),
    "Enter Fullscreen": t("Full screen"),
    "Exit Fullscreen": t("Exit full screen"),
  };
}

const lightboxPlugins = [Counter, Fullscreen, Zoom];

/** Justified rows of photos; a click opens the lightbox (swipe, zoom, full screen). */
export function PhotoAlbum({ images }: { images: GalleryImage[] }) {
  const [index, setIndex] = useState(-1);
  const labels = useLightboxLabels();
  const photos = images.map(toAlbumPhoto);

  if (!photos.length) return null;
  return (
    <>
      <RowsPhotoAlbum
        photos={photos}
        targetRowHeight={220}
        defaultContainerWidth={1200}
        sizes={{
          size: "1200px",
          sizes: [{ viewport: "(max-width: 1280px)", size: "calc(100vw - 32px)" }],
        }}
        spacing={8}
        onClick={({ index: clicked }) => setIndex(clicked)}
      />
      <Lightbox
        open={index >= 0}
        index={Math.max(index, 0)}
        close={() => setIndex(-1)}
        slides={photos.map((photo) => ({ ...photo, src: photo.large }))}
        plugins={lightboxPlugins}
        labels={labels}
      />
    </>
  );
}

/**
 * Photo album that loads more pages while the visitor scrolls
 * (react-photo-album's `InfiniteScroll` watches the end of the list with an IntersectionObserver).
 */
export function InfinitePhotoAlbum({
  initial,
  hasMore,
  loadPage,
  loading,
  finished,
}: {
  initial: GalleryImage[];
  hasMore: boolean;
  /** Images of API page `n` (2, 3, ...) and whether more pages follow. */
  loadPage: (page: number) => Promise<{ images: GalleryImage[]; hasMore: boolean }>;
  loading: React.ReactNode;
  finished: React.ReactNode;
}) {
  const [slides, setSlides] = useState<SlidePhoto[]>([]);
  const [index, setIndex] = useState(-1);
  const labels = useLightboxLabels();
  const more = useRef(hasMore);

  return (
    <>
      <InfiniteScroll<SlidePhoto>
        photos={initial.map(toAlbumPhoto)}
        fetch={async (batches) => {
          // `batches` already loaded, the initial page included; the API counts pages from 1.
          if (!more.current) return null;
          const page = await loadPage(batches + 1);
          more.current = page.hasMore;
          return page.images.map(toAlbumPhoto);
        }}
        onClick={({ photos, index: clicked }) => {
          setSlides([...photos]);
          setIndex(clicked);
        }}
        loading={loading}
        finished={finished}
      >
        <RowsPhotoAlbum
          photos={[]}
          targetRowHeight={220}
          defaultContainerWidth={1200}
          sizes={{
            size: "1200px",
            sizes: [{ viewport: "(max-width: 1280px)", size: "calc(100vw - 32px)" }],
          }}
          spacing={8}
        />
      </InfiniteScroll>
      <Lightbox
        open={index >= 0}
        index={Math.max(index, 0)}
        close={() => setIndex(-1)}
        slides={slides.map((photo) => ({ ...photo, src: photo.large }))}
        plugins={lightboxPlugins}
        labels={labels}
      />
    </>
  );
}
