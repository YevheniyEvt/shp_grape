import { describe, expect, it } from "vitest";

import { compilePluralFormula, createTranslator, interpolate, type DjangoCatalog } from "./gettext";

// Plural formula Django ships for Ukrainian (4 forms; the last one is for fractions).
const UK_PLURAL =
  "(n % 1 == 0 && n % 10 == 1 && n % 100 != 11 ? 0 : n % 1 == 0 && n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 12 || n % 100 > 14) ? 1 : n % 1 == 0 && (n % 10 ==0 || (n % 10 >=5 && n % 10 <=9) || (n % 100 >=11 && n % 100 <=14 )) ? 2: 3)";

const ukCatalog: DjangoCatalog = {
  catalog: {
    Catalog: "Каталог",
    "Hello %(name)s": "Привіт, %(name)s",
    "%(count)s variety": [
      "%(count)s сорт",
      "%(count)s сорти",
      "%(count)s сортів",
      "%(count)s сорту",
    ],
    "month\u0004May": "Травень",
  },
  plural: UK_PLURAL,
};

describe("interpolate", () => {
  it("substitutes named placeholders", () => {
    expect(interpolate("%(a)s and %(b)s", { a: 1, b: "two" })).toBe("1 and two");
  });

  it("substitutes positional placeholders", () => {
    expect(interpolate("%s of %s", [3, 10])).toBe("3 of 10");
  });

  it("leaves unknown named placeholders untouched", () => {
    expect(interpolate("%(missing)s", { other: 1 })).toBe("%(missing)s");
  });

  it("returns the format unchanged without values", () => {
    expect(interpolate("100%(x)s")).toBe("100%(x)s");
  });
});

describe("compilePluralFormula", () => {
  it.each([
    [1, 0],
    [2, 1],
    [5, 2],
    [11, 2],
    [21, 0],
    [22, 1],
    [1.5, 3],
  ])("Ukrainian rule maps %s to form %s", (n, form) => {
    expect(compilePluralFormula(UK_PLURAL)(n)).toBe(form);
  });

  it("falls back to the Germanic rule without a formula", () => {
    const plural = compilePluralFormula(null);
    expect([plural(1), plural(0), plural(2)]).toEqual([0, 1, 1]);
  });

  it("rejects formulas with unexpected characters", () => {
    const plural = compilePluralFormula("alert(1)");
    expect(plural(1)).toBe(0);
    expect(plural(5)).toBe(1);
  });

  it("falls back on a syntactically broken formula", () => {
    expect(compilePluralFormula("n ? (")(2)).toBe(1);
  });
});

describe("createTranslator", () => {
  const { t, nt, pt } = createTranslator(ukCatalog);

  it("translates known strings", () => {
    expect(t("Catalog")).toBe("Каталог");
  });

  it("falls back to the msgid for missing strings", () => {
    expect(t("Not translated")).toBe("Not translated");
  });

  it("interpolates after translating", () => {
    expect(t("Hello %(name)s", { name: "Олена" })).toBe("Привіт, Олена");
  });

  it.each([
    [1, "1 сорт"],
    [3, "3 сорти"],
    [7, "7 сортів"],
    [21, "21 сорт"],
  ])("picks the Ukrainian plural form for %s", (count, expected) => {
    expect(nt("%(count)s variety", "%(count)s varieties", count, { count })).toBe(expected);
  });

  it("uses English plural fallback for untranslated plurals", () => {
    expect(nt("%s item", "%s items", 1, [1])).toBe("1 item");
    expect(nt("%s item", "%s items", 4, [4])).toBe("4 items");
  });

  it("translates with context and falls back without it", () => {
    expect(pt("month", "May")).toBe("Травень");
    expect(pt("verb", "May")).toBe("May");
  });

  it("works with an empty catalog", () => {
    const empty = createTranslator(undefined);
    expect(empty.t("Catalog")).toBe("Catalog");
    expect(empty.nt("a", "b", 2)).toBe("b");
  });
});
