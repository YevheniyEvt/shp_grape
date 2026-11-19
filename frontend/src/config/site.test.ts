import { describe, expect, it } from "vitest";

import { createTranslator } from "@/i18n/gettext";

import { getMainNav, mapEmbedUrl, phoneHref, siteName } from "./site";

describe("phoneHref", () => {
  it("keeps only digits and the plus sign", () => {
    expect(phoneHref("+380 (50) 123-45-67")).toBe("tel:+380501234567");
  });
});

describe("getMainNav", () => {
  it("translates labels and starts with the home page", () => {
    const nav = getMainNav(createTranslator({ catalog: { Home: "Головна" }, plural: null }));
    expect(nav[0]).toEqual({ href: "/", label: "Головна" });
    expect(nav.map((item) => item.href)).toContain("/catalog");
  });
});

describe("siteName", () => {
  const t = createTranslator({ catalog: { Vineyard: "Виноградник" }, plural: null });

  it("prefers the name from the admin and falls back to the translated default", () => {
    expect(siteName("Сад Олени", t)).toBe("Сад Олени");
    expect(siteName("  ", t)).toBe("Виноградник");
    expect(siteName(undefined, t)).toBe("Виноградник");
  });
});

describe("mapEmbedUrl", () => {
  it("embeds a point in the visitor's language", () => {
    expect(mapEmbedUrl({ latitude: 49, longitude: 31.4 }, "en")).toBe(
      "https://maps.google.com/maps?q=49%2C31.4&z=13&hl=en&output=embed",
    );
  });
});
