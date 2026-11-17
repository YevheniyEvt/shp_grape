import { describe, expect, it } from "vitest";

import { createTranslator } from "@/i18n/gettext";

import { getMainNav, phoneHref } from "./site";

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
