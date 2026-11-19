/**
 * Site-wide settings edited in the Django admin (`/api/content/settings/`).
 */

import { cacheLife } from "next/cache";

import type { components } from "@/types/api";

import { apiFetch } from "./api";

export type SiteSettings = components["schemas"]["SiteSettings"];

/** Used when the API is unreachable: the built-in background keeps the site looking right. */
export const DEFAULT_SITE_SETTINGS: SiteSettings = {
  show_background: true,
  background_image: null,
};

/** Site settings, cached between requests (admin changes show up within minutes). */
export async function getSiteSettings(): Promise<SiteSettings> {
  "use cache";
  cacheLife("minutes");
  try {
    return await apiFetch<SiteSettings>("/api/content/settings/");
  } catch {
    return DEFAULT_SITE_SETTINGS;
  }
}
