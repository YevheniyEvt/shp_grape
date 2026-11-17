import { defaultLocale, isLocale, localizePath, splitLocale } from "./config";

/** What the proxy should do with an incoming request path. */
export type LocaleRouteAction =
  { type: "next" } | { type: "rewrite"; pathname: string } | { type: "redirect"; pathname: string };

/**
 * Decide how to route a request so that:
 * - the default locale is served without a prefix (`/catalog` renders `/uk/catalog`);
 * - an explicit default-locale prefix redirects to the canonical URL (`/uk/x` -> `/x`);
 * - other locales are served as-is (`/en/x`);
 * - an unprefixed URL redirects to the visitor's saved non-default locale, if any.
 */
export function resolveLocaleRoute(
  pathname: string,
  savedLocale: string | undefined,
): LocaleRouteAction {
  const { locale, path } = splitLocale(pathname);

  if (locale === defaultLocale) {
    return { type: "redirect", pathname: path };
  }
  if (locale !== null) {
    return { type: "next" };
  }
  if (isLocale(savedLocale) && savedLocale !== defaultLocale) {
    return { type: "redirect", pathname: localizePath(path, savedLocale) };
  }
  return { type: "rewrite", pathname: `/${defaultLocale}${path === "/" ? "" : path}` };
}
