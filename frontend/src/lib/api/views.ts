/**
 * Browser-side catalog calls. Kept apart from `catalog.ts`, whose cached server functions
 * cannot be imported into Client Components.
 */

import type { components } from "@/types/api";

import { apiUrl } from "./client";

type FeedPhoto = components["schemas"]["FeedPhoto"];

/** Register a page view; failures are ignored, the counter is not critical. */
export async function registerView(slug: string): Promise<void> {
  try {
    await fetch(apiUrl(`/api/catalog/varieties/${encodeURIComponent(slug)}/view/`), {
      method: "POST",
    });
  } catch {
    // Network errors must not break the page.
  }
}

/** One page of the "All photos" feed, fetched by the browser while scrolling. */
export async function fetchPhotoFeedPage(
  page: number,
  locale: string,
): Promise<{ next_page: number | null; results: FeedPhoto[] }> {
  const response = await fetch(apiUrl(`/api/content/gallery/photos/?page=${page}`), {
    headers: { Accept: "application/json", "Accept-Language": locale },
  });
  if (!response.ok) throw new Error(`Photo feed request failed: ${response.status}`);
  return response.json();
}
