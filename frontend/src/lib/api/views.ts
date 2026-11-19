/**
 * Browser-side catalog calls. Kept apart from `catalog.ts`, whose cached server functions
 * cannot be imported into Client Components.
 */

import { apiUrl } from "./client";

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
