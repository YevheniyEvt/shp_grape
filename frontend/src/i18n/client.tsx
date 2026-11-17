"use client";

import { createContext, useContext, useMemo, type ReactNode } from "react";

import { localeCookie, localizePath, type Locale } from "./config";
import { createTranslator, type DjangoCatalog, type Translator } from "./gettext";

type I18nContextValue = Translator & {
  locale: Locale;
  /** Public URL of `path` in the active locale. */
  href: (path: string) => string;
};

const I18nContext = createContext<I18nContextValue | null>(null);

export function I18nProvider({
  locale,
  catalog,
  children,
}: {
  locale: Locale;
  catalog: DjangoCatalog;
  children: ReactNode;
}) {
  const value = useMemo<I18nContextValue>(
    () => ({
      ...createTranslator(catalog),
      locale,
      href: (path: string) => localizePath(path, locale),
    }),
    [catalog, locale],
  );
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

/** Translator and locale helpers for Client Components. */
export function useT(): I18nContextValue {
  const value = useContext(I18nContext);
  if (!value) throw new Error("useT() must be used inside <I18nProvider>");
  return value;
}

/** Persist the visitor's language choice so unprefixed URLs open in that language. */
export function rememberLocale(locale: Locale): void {
  document.cookie = localeCookie(locale);
}
