import Image from "next/image";
import Link from "next/link";

import { localizePath, type Locale } from "@/i18n/config";
import { getRandomPhotos, type RandomPhoto } from "@/lib/api/catalog";

export const RANDOM_PHOTOS_LIMIT = 8;

/** Photos for the footer strip; the footer must render even when the API is down. */
export async function loadRandomPhotos(locale: Locale): Promise<RandomPhoto[]> {
  try {
    return await getRandomPhotos(locale, RANDOM_PHOTOS_LIMIT);
  } catch {
    return [];
  }
}

/** Thumbnails of random variety photos, each linking to its variety. */
export function RandomPhotos({
  photos,
  locale,
  title,
}: {
  photos: RandomPhoto[];
  locale: Locale;
  title: string;
}) {
  if (!photos.length) return null;
  return (
    <section aria-label={title} className="mt-6">
      <h2 className="mb-3 text-sm font-semibold">{title}</h2>
      <ul className="grid grid-cols-4 gap-2 sm:max-w-md">
        {photos.map((photo) => (
          <li key={photo.id}>
            <Link
              href={localizePath(`/catalog/${photo.variety.slug}`, locale)}
              title={photo.variety.name}
              className="block overflow-hidden rounded-md ring-1 ring-foreground/10 transition hover:opacity-80"
            >
              <Image
                src={photo.thumb}
                alt={photo.alt}
                width={photo.width ?? 400}
                height={photo.height ?? 300}
                sizes="96px"
                unoptimized
                className="aspect-square object-cover"
              />
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
