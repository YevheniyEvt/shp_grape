/**
 * Locale configuration shared by the proxy, server and client code.
 *
 * Keep in sync with Django `settings.LANGUAGES`. The default locale is served
 * without a URL prefix (`/catalog`), other locales with one (`/en/catalog`).
 */

export const locales = ["uk", "en"] as const;
export type Locale = (typeof locales)[number];

export const defaultLocale: Locale = "uk";

/** Cookie that remembers the visitor's explicit language choice. */
export const LOCALE_COOKIE = "NEXT_LOCALE";
export const LOCALE_COOKIE_MAX_AGE = 60 * 60 * 24 * 365;

export function isLocale(value: string | undefined | null): value is Locale {
  return locales.includes(value as Locale);
}

/** Split a pathname into its locale prefix (if any) and the rest of the path. */
export function splitLocale(pathname: string): { locale: Locale | null; path: string } {
  const match = /^\/([^/]+)(\/.*)?$/.exec(pathname);
  if (match && isLocale(match[1])) {
    return { locale: match[1], path: match[2] || "/" };
  }
  return { locale: null, path: pathname || "/" };
}

/** Build the public URL of `path` in `locale` (no prefix for the default locale). */
export function localizePath(path: string, locale: Locale): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  if (locale === defaultLocale) return normalized;
  return normalized === "/" ? `/${locale}` : `/${locale}${normalized}`;
}

/** `document.cookie` value that remembers `locale` as the visitor's choice. */
export function localeCookie(locale: Locale): string {
  return `${LOCALE_COOKIE}=${locale}; path=/; max-age=${LOCALE_COOKIE_MAX_AGE}; samesite=lax`;
}

/** Return the same page in another locale, keeping path, query and hash. */
export function switchLocaleHref(currentHref: string, target: Locale): string {
  const url = new URL(currentHref, "http://localhost");
  const { path } = splitLocale(url.pathname);
  return localizePath(path, target) + url.search + url.hash;
}
