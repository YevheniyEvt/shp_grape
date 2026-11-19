import { describe, expect, it } from "vitest";

import {
  formatDate,
  formatNumber,
  formatPrice,
  formatRange,
  lowestPrice,
  pageNumber,
  plainText,
} from "./format";

// Intl inserts non-breaking spaces; compare with plain ones.
const plain = (value: string | null) => value?.replace(/\s/g, " ");

describe("format", () => {
  it("formats numbers with the locale's decimal separator", () => {
    expect(formatNumber(0.5, "uk")).toBe("0,5");
    expect(formatNumber(0.5, "en")).toBe("0.5");
  });

  it("formats prices in hryvnias", () => {
    expect(plain(formatPrice(1200, "uk"))).toBe("1 200 ₴");
    expect(plain(formatPrice(30, "en"))).toBe("UAH 30");
  });

  it("formats ranges", () => {
    expect(formatRange(0.5, 0.8, "uk")).toBe("0,5–0,8");
    expect(formatRange(8, 8, "en")).toBe("8");
    expect(formatRange(8, null, "en")).toBe("8");
    expect(formatRange(undefined, 9, "en")).toBe("9");
    expect(formatRange(null, null, "en")).toBeNull();
  });

  it("finds the lowest known price", () => {
    expect(lowestPrice([120, 30])).toBe(30);
    expect(lowestPrice([null, 90])).toBe(90);
    expect(lowestPrice([null, undefined])).toBeNull();
  });
});

describe("plainText", () => {
  it("strips tags and cuts long text", () => {
    expect(plainText("<p>Very <b>early</b></p><p>variety</p>", 100)).toBe("Very early variety");
    expect(plainText("<p>abcdef ghij</p>", 8)).toBe("abcdef…");
    expect(plainText(null, 10)).toBe("");
  });
});

describe("formatDate / pageNumber", () => {
  it("formats ISO dates for the locale", () => {
    expect(formatDate("2026-11-19", "uk")).toBe("19 листопада 2026 р.");
    expect(formatDate("2026-01-02", "en")).toBe("January 2, 2026");
  });

  it("reads the page number", () => {
    expect(pageNumber("3")).toBe(3);
    expect(pageNumber(["2", "5"])).toBe(2);
    expect(pageNumber("0")).toBe(1);
    expect(pageNumber("x")).toBe(1);
    expect(pageNumber(undefined)).toBe(1);
  });
});
