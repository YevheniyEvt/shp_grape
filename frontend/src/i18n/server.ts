/**
 * Server-side i18n helpers. Usable only in Server Components and server utilities
 * (`next/root-params` fails the build if imported from a Client Component).
 */

import { cacheLife } from "next/cache";
import { notFound } from "next/navigation";
import { lang } from "next/root-params";

import { apiFetch } from "@/lib/api";

import { isLocale, localizePath, type Locale } from "./config";
import { createTranslator, type DjangoCatalog, type Translator } from "./gettext";

export type SiteLanguage = { code: Locale; name: string; is_default: boolean };

/** Active locale from the `[lang]` root segment; unknown values render 404. */
export async function getLocale(): Promise<Locale> {
  const value = await lang();
  if (!isLocale(value)) notFound();
  return value;
}

/** Compiled `djangojs` catalog for a locale, cached between requests. */
export async function getCatalog(locale: Locale): Promise<DjangoCatalog> {
  "use cache";
  cacheLife("minutes");
  return apiFetch<DjangoCatalog>(`/api/i18n/${locale}/`, { locale });
}

/** Site languages for the language switcher. */
export async function getLanguages(): Promise<SiteLanguage[]> {
  "use cache";
  cacheLife("hours");
  return apiFetch<SiteLanguage[]>("/api/i18n/languages/");
}

/** Translator (`t`, `nt`, `pt`) for the active locale. */
export async function getTranslator(): Promise<Translator & { locale: Locale }> {
  const locale = await getLocale();
  return { ...createTranslator(await getCatalog(locale)), locale };
}

/** Public URL of `path` in the active locale. */
export async function localizedHref(path: string): Promise<string> {
  return localizePath(path, await getLocale());
}
