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
