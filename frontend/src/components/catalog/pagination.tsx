import { ChevronLeftIcon, ChevronRightIcon } from "lucide-react";
import Link from "next/link";

import type { Translator } from "@/i18n/gettext";
import { type CatalogQuery, catalogHref, withPage } from "@/lib/catalog-query";
import { cn } from "@/lib/utils";

export type PageItem = number | "gap";

/** Page numbers to show: first, last and a window around the current page, with gaps. */
export function pageItems(current: number, total: number, around = 1): PageItem[] {
  const pages = new Set([1, total]);
  for (let page = current - around; page <= current + around; page++) {
    if (page >= 1 && page <= total) pages.add(page);
  }
  const sorted = [...pages].filter((page) => page >= 1).sort((a, b) => a - b);
  const items: PageItem[] = [];
  sorted.forEach((page, index) => {
    const previous = sorted[index - 1];
    if (previous !== undefined && page - previous === 2) items.push(previous + 1);
    else if (previous !== undefined && page - previous > 2) items.push("gap");
    items.push(page);
  });
  return items;
}

const itemClass =
  "inline-flex h-9 min-w-9 items-center justify-center rounded-md px-3 text-sm font-medium";

/** Plain links (crawlable, work without JavaScript); the current page is not a link. */
export function Pagination({
  query,
  totalPages,
  basePath,
  t,
}: {
  query: CatalogQuery;
  totalPages: number;
  basePath: string;
  t: Translator["t"];
}) {
  if (totalPages <= 1) return null;
  const current = Math.min(query.page, totalPages);
  const href = (page: number) => catalogHref(basePath, withPage(query, page));

  return (
    <nav aria-label={t("Pages")} className="flex flex-wrap items-center justify-center gap-1">
      {current > 1 && (
        <Link href={href(current - 1)} rel="prev" className={cn(itemClass, "hover:bg-muted")}>
          <ChevronLeftIcon className="size-4" aria-hidden="true" />
          <span className="sr-only sm:not-sr-only">{t("Previous")}</span>
        </Link>
      )}
      {pageItems(current, totalPages).map((item, index) =>
        item === "gap" ? (
          <span key={`gap-${index}`} className={cn(itemClass, "text-muted-foreground")}>
            …
          </span>
        ) : item === current ? (
          <span
            key={item}
            aria-current="page"
            className={cn(itemClass, "bg-primary text-primary-foreground")}
          >
            {item}
          </span>
        ) : (
          <Link key={item} href={href(item)} className={cn(itemClass, "hover:bg-muted")}>
            {item}
          </Link>
        ),
      )}
      {current < totalPages && (
        <Link href={href(current + 1)} rel="next" className={cn(itemClass, "hover:bg-muted")}>
          <span className="sr-only sm:not-sr-only">{t("Next")}</span>
          <ChevronRightIcon className="size-4" aria-hidden="true" />
        </Link>
      )}
    </nav>
  );
}
