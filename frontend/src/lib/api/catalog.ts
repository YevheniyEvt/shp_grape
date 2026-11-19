/**
 * Catalog API (`/api/catalog/`). Server-side reads are cached for a few minutes, so admin
 * changes show up quickly while repeated visits do not hit Django.
 */

import { cacheLife } from "next/cache";

import type { Locale } from "@/i18n/config";
import { CATALOG_PAGE_SIZE } from "@/lib/catalog-query";
import type { components } from "@/types/api";

import { ApiError, apiFetch } from "./client";

type Schemas = components["schemas"];
export type VarietyListItem = Schemas["VarietyList"];
export type VarietyDetail = Schemas["VarietyDetail"];
export type VarietyPage = Schemas["PaginatedVarietyListList"];
export type Photo = Schemas["Photo"];
export type RandomPhoto = Schemas["RandomPhoto"];
export type FilterOptions = Schemas["FilterOptions"];
export type Dictionary = Schemas["Dictionary"];
export type Video = Schemas["Video"];

const EMPTY_PAGE: VarietyPage = { count: 0, next: null, previous: null, results: [] };

/** Treat "not found" as a value: a missing variety or a page past the end. */
async function orNull<T>(request: Promise<T>): Promise<T | null> {
  try {
    return await request;
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

/** One page of the variety list; `query` is the canonical string from `toSearchParams`. */
export async function getVarieties(locale: Locale, query: string): Promise<VarietyPage> {
  "use cache";
  cacheLife("minutes");
  const params = new URLSearchParams(query);
  params.set("page_size", String(CATALOG_PAGE_SIZE));
  const page = await orNull(apiFetch<VarietyPage>(`/api/catalog/varieties/?${params}`, { locale }));
  return page ?? EMPTY_PAGE;
}

export async function getVariety(locale: Locale, slug: string): Promise<VarietyDetail | null> {
  "use cache";
  cacheLife("minutes");
  return orNull(
    apiFetch<VarietyDetail>(`/api/catalog/varieties/${encodeURIComponent(slug)}/`, { locale }),
  );
}

export async function getFilterOptions(locale: Locale): Promise<FilterOptions> {
  "use cache";
  cacheLife("minutes");
  return apiFetch<FilterOptions>("/api/catalog/filters/", { locale });
}

/** Letters of the current language that have published varieties. */
export async function getLetters(locale: Locale): Promise<string[]> {
  "use cache";
  cacheLife("minutes");
  return apiFetch<string[]>("/api/catalog/letters/", { locale });
}

/** Same as `getLetters`, or null when the API cannot tell (then every letter stays a link). */
export async function getAvailableLetters(locale: Locale): Promise<string[] | null> {
  try {
    return await getLetters(locale);
  } catch {
    return null;
  }
}

export async function getRandomPhotos(locale: Locale, limit: number): Promise<RandomPhoto[]> {
  "use cache";
  cacheLife("minutes");
  return apiFetch<RandomPhoto[]>(`/api/catalog/photos/random/?limit=${limit}`, { locale });
}
