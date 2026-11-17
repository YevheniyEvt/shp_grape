import { describe, expect, it } from "vitest";

import { getAlphabet } from "./alphabet";
import {
  LOCALE_COOKIE,
  isLocale,
  localeCookie,
  localizePath,
  splitLocale,
  switchLocaleHref,
} from "./config";
import { resolveLocaleRoute } from "./routing";

describe("isLocale", () => {
  it.each([
    ["uk", true],
    ["en", true],
    ["de", false],
    ["", false],
    [undefined, false],
  ])("%s -> %s", (value, expected) => {
    expect(isLocale(value)).toBe(expected);
  });
});

describe("splitLocale", () => {
  it.each([
    ["/en/catalog/some-variety", "en", "/catalog/some-variety"],
    ["/en", "en", "/"],
    ["/en/", "en", "/"],
    ["/uk/news", "uk", "/news"],
    ["/catalog", null, "/catalog"],
    ["/english", null, "/english"],
    ["/", null, "/"],
  ])("%s", (pathname, locale, path) => {
    expect(splitLocale(pathname)).toEqual({ locale, path });
  });
});

describe("localizePath", () => {
  it.each([
    ["/catalog", "uk", "/catalog"],
    ["/", "uk", "/"],
    ["/catalog", "en", "/en/catalog"],
    ["/", "en", "/en"],
    ["news", "en", "/en/news"],
  ] as const)("%s in %s -> %s", (path, locale, expected) => {
    expect(localizePath(path, locale)).toBe(expected);
  });
});

describe("switchLocaleHref", () => {
  it("keeps path, query and hash", () => {
    expect(switchLocaleHref("http://site.test/catalog?letter=А#top", "en")).toBe(
      "/en/catalog?letter=%D0%90#top",
    );
  });

  it("drops the prefix when switching to the default locale", () => {
    expect(switchLocaleHref("http://site.test/en/news", "uk")).toBe("/news");
    expect(switchLocaleHref("http://site.test/en", "uk")).toBe("/");
  });
});

describe("localeCookie", () => {
  it("builds a long-lived site-wide cookie", () => {
    const cookie = localeCookie("en");
    expect(cookie.startsWith(`${LOCALE_COOKIE}=en;`)).toBe(true);
    expect(cookie).toContain("path=/");
    expect(cookie).toContain("samesite=lax");
  });
});

describe("resolveLocaleRoute", () => {
  it("rewrites unprefixed paths to the default locale", () => {
    expect(resolveLocaleRoute("/catalog", undefined)).toEqual({
      type: "rewrite",
      pathname: "/uk/catalog",
    });
    expect(resolveLocaleRoute("/", undefined)).toEqual({ type: "rewrite", pathname: "/uk" });
  });

  it("redirects an explicit default-locale prefix to the canonical URL", () => {
    expect(resolveLocaleRoute("/uk/catalog", undefined)).toEqual({
      type: "redirect",
      pathname: "/catalog",
    });
  });

  it("passes other locales through", () => {
    expect(resolveLocaleRoute("/en/catalog", "uk")).toEqual({ type: "next" });
  });

  it("redirects to the saved non-default locale", () => {
    expect(resolveLocaleRoute("/news", "en")).toEqual({ type: "redirect", pathname: "/en/news" });
  });

  it("ignores a saved default or unknown locale", () => {
    expect(resolveLocaleRoute("/news", "uk").type).toBe("rewrite");
    expect(resolveLocaleRoute("/news", "de").type).toBe("rewrite");
  });

  it("treats an unknown prefix as a normal path (404 later)", () => {
    expect(resolveLocaleRoute("/de/news", undefined)).toEqual({
      type: "rewrite",
      pathname: "/uk/de/news",
    });
  });
});

describe("getAlphabet", () => {
  it("returns Ukrainian letters including Ґ, Є, І, Ї", () => {
    const letters = getAlphabet("uk");
    expect(letters).toHaveLength(32);
    expect(letters).toEqual(expect.arrayContaining(["Ґ", "Є", "І", "Ї"]));
  });

  it("returns the Latin alphabet for English", () => {
    expect(getAlphabet("en")).toHaveLength(26);
  });
});
