/** Number and price formatting for the active locale. */

import type { Locale } from "@/i18n/config";

type Num = number | null | undefined;

const isNumber = (value: Num): value is number => typeof value === "number";

export function formatNumber(value: number, locale: Locale): string {
  return new Intl.NumberFormat(locale, { maximumFractionDigits: 2 }).format(value);
}

/** Price in hryvnias without kopecks: `30 ₴` / `UAH 30`. */
export function formatPrice(value: number, locale: Locale): string {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency: "UAH",
    currencyDisplay: locale === "uk" ? "symbol" : "code",
    maximumFractionDigits: 0,
  }).format(value);
}

/** `0,5–0,8`, `0,5` (equal or one bound), or null when both bounds are empty. */
export function formatRange(min: Num, max: Num, locale: Locale): string | null {
  if (isNumber(min) && isNumber(max)) {
    return min === max
      ? formatNumber(min, locale)
      : `${formatNumber(min, locale)}–${formatNumber(max, locale)}`;
  }
  if (isNumber(min)) return formatNumber(min, locale);
  if (isNumber(max)) return formatNumber(max, locale);
  return null;
}

/** Lowest known price of a variety (cutting or sapling), for the "from" label. */
export function lowestPrice(prices: Num[]): number | null {
  const known = prices.filter(isNumber);
  return known.length ? Math.min(...known) : null;
}

/** Text of an HTML fragment, collapsed and cut to `limit` characters (for meta descriptions). */
export function plainText(html: string | null | undefined, limit: number): string {
  const text = (html ?? "")
    .replace(/<[^>]*>/g, " ")
    .replace(/&nbsp;/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  if (text.length <= limit) return text;
  return `${text.slice(0, limit - 1).trimEnd()}…`;
}

/** `19 листопада 2026 р.` / `November 19, 2026` from an ISO date (`2026-11-19`). */
export function formatDate(isoDate: string, locale: Locale): string {
  const [year, month, day] = isoDate.split("-").map(Number);
  // Noon UTC keeps the calendar day the same in every time zone.
  const date = new Date(Date.UTC(year, month - 1, day, 12));
  return new Intl.DateTimeFormat(locale, { dateStyle: "long", timeZone: "UTC" }).format(date);
}

/** Page number from a `?page=` value: a positive integer, 1 otherwise. */
export function pageNumber(value: string | string[] | undefined): number {
  const page = Number(Array.isArray(value) ? value[0] : value);
  return Number.isInteger(page) && page > 1 ? page : 1;
}
