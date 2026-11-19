import { GrapeIcon } from "lucide-react";
import Image from "next/image";

import type { Photo } from "@/lib/api/catalog";
import { cn } from "@/lib/utils";

type Rendition = "thumb" | "medium" | "large";

/**
 * A variety photo in one of the imagekit renditions, or a grape placeholder.
 *
 * Fixed `width`/`height` from the API reserve the space, so the layout does not jump while
 * the image loads. The renditions are already resized WebP files, hence `unoptimized`.
 */
export function VarietyImage({
  photo,
  rendition = "thumb",
  className,
  sizes,
  preload = false,
}: {
  photo: Photo | null | undefined;
  rendition?: Rendition;
  className?: string;
  sizes?: string;
  preload?: boolean;
}) {
  if (!photo) {
    return (
      <div
        data-testid="photo-placeholder"
        className={cn("flex items-center justify-center bg-muted text-primary/40", className)}
      >
        <GrapeIcon className="size-1/4" aria-hidden="true" />
      </div>
    );
  }
  return (
    <Image
      src={photo[rendition]}
      alt={photo.alt}
      width={photo.width ?? 1200}
      height={photo.height ?? 900}
      sizes={sizes}
      preload={preload}
      unoptimized
      className={cn("object-cover", className)}
    />
  );
}
