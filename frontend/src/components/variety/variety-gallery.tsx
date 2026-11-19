"use client";

import { ExpandIcon } from "lucide-react";
import { useState } from "react";
import Lightbox from "yet-another-react-lightbox";
import Counter from "yet-another-react-lightbox/plugins/counter";
import Fullscreen from "yet-another-react-lightbox/plugins/fullscreen";
import Zoom from "yet-another-react-lightbox/plugins/zoom";
import "yet-another-react-lightbox/styles.css";
import "yet-another-react-lightbox/plugins/counter.css";

import { VarietyImage } from "@/components/catalog/variety-image";
import { useT } from "@/i18n/client";
import type { Photo } from "@/lib/api/catalog";
import { cn } from "@/lib/utils";

/**
 * Large photo with a thumbnail strip; clicking the photo opens a lightbox
 * (swipe, zoom, full screen, counter, keyboard arrows and Escape).
 */
export function VarietyGallery({ photos, name }: { photos: Photo[]; name: string }) {
  const { t } = useT();
  const [current, setCurrent] = useState(0);
  const [open, setOpen] = useState(false);

  if (!photos.length) {
    return <VarietyImage photo={null} className="aspect-4/3 w-full rounded-xl" />;
  }
  const photo = photos[current];

  return (
    <div className="grid gap-3">
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="group relative overflow-hidden rounded-xl bg-muted"
        aria-label={t("Open photo %(number)s of %(total)s", {
          number: current + 1,
          total: photos.length,
        })}
      >
        <VarietyImage
          photo={photo}
          rendition="medium"
          className="aspect-4/3 w-full"
          sizes="(min-width: 1024px) 50vw, 100vw"
          preload
        />
        <span className="absolute right-3 bottom-3 rounded-full bg-background/80 p-2 opacity-0 transition-opacity group-hover:opacity-100 print:hidden">
          <ExpandIcon className="size-4" aria-hidden="true" />
        </span>
      </button>

      {photos.length > 1 && (
        <ul
          className="flex gap-2 overflow-x-auto pb-1 print:hidden"
          aria-label={t("Photos of %(name)s", { name })}
        >
          {photos.map((item, index) => (
            <li key={item.id} className="shrink-0">
              <button
                type="button"
                onClick={() => setCurrent(index)}
                aria-current={index === current}
                aria-label={t("Show photo %(number)s", { number: index + 1 })}
                className={cn(
                  "block overflow-hidden rounded-md ring-2 ring-transparent transition",
                  index === current ? "ring-primary" : "opacity-70 hover:opacity-100",
                )}
              >
                <VarietyImage photo={item} className="h-16 w-20" sizes="80px" />
              </button>
            </li>
          ))}
        </ul>
      )}

      <Lightbox
        open={open}
        close={() => setOpen(false)}
        index={current}
        on={{ view: ({ index }) => setCurrent(index) }}
        slides={photos.map((item) => ({
          src: item.large,
          alt: item.alt,
          width: item.width ?? undefined,
          height: item.height ?? undefined,
        }))}
        plugins={[Counter, Fullscreen, Zoom]}
        labels={{
          Previous: t("Previous"),
          Next: t("Next"),
          Close: t("Close"),
          "Zoom in": t("Zoom in"),
          "Zoom out": t("Zoom out"),
          "Enter Fullscreen": t("Full screen"),
          "Exit Fullscreen": t("Exit full screen"),
        }}
      />
    </div>
  );
}
