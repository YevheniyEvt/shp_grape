import { SearchXIcon, XIcon } from "lucide-react";
import Link from "next/link";

import { Pagination } from "@/components/common/pagination";
import { Button } from "@/components/ui/button";
import { getAlphabet } from "@/i18n/alphabet";
import { localizePath } from "@/i18n/config";
import { getTranslator } from "@/i18n/server";
import { getAvailableLetters, getFilterOptions, getVarieties } from "@/lib/api/catalog";
import {
  CATALOG_PAGE_SIZE,
  catalogHref,
  hasFilters,
  parseCatalogQuery,
  type RawSearchParams,
  resetFilters,
  toSearchParams,
  updateQuery,
  withPage,
} from "@/lib/catalog-query";

import { AlphabetBar } from "./alphabet-bar";
import { CatalogSearch } from "./catalog-search";
import { FiltersPanel, MobileFilters } from "./filters-panel";
import { SortSelect } from "./sort-select";
import { VarietyCard } from "./variety-card";

/**
 * The dynamic part of the catalog: reads `searchParams`, so it renders per request
 * inside a Suspense boundary while the page title stays in the static shell.
 */
export async function CatalogResults({ searchParams }: { searchParams: Promise<RawSearchParams> }) {
  const { t, nt, locale } = await getTranslator();
  const query = parseCatalogQuery(await searchParams);
  const basePath = localizePath("/catalog", locale);

  const [page, options, letters] = await Promise.all([
    getVarieties(locale, toSearchParams(query).toString()),
    getFilterOptions(locale),
    getAvailableLetters(locale),
  ]);
  const totalPages = Math.ceil(page.count / CATALOG_PAGE_SIZE);
  const href = (path: string) => localizePath(path, locale);

  return (
    <div className="grid gap-6">
      {/* On wider screens the header already shows the alphabet. */}
      <AlphabetBar
        className="md:hidden"
        label={t("Varieties by letter")}
        letters={getAlphabet(locale)}
        available={letters}
        active={query.letter}
        hrefFor={(letter) =>
          catalogHref(
            basePath,
            updateQuery(query, { letter: letter === query.letter ? undefined : letter }),
          )
        }
      />

      <div className="flex flex-wrap items-center gap-3 rounded-xl bg-card/95 p-3 shadow-sm ring-1 ring-foreground/10">
        <CatalogSearch query={query} basePath={basePath} />
        <MobileFilters query={query} options={options} basePath={basePath} />
        {query.letter && (
          <Link
            href={catalogHref(basePath, updateQuery(query, { letter: undefined }))}
            aria-label={t("Remove the letter filter")}
            className="inline-flex items-center gap-1 rounded-full bg-primary px-3 py-1 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            {t("Letter: %(letter)s", { letter: query.letter })}
            <XIcon className="size-3.5" aria-hidden="true" />
          </Link>
        )}
        <p className="text-sm text-muted-foreground" aria-live="polite">
          {nt("%(count)s variety", "%(count)s varieties", page.count, { count: page.count })}
        </p>
        <div className="ml-auto">
          <SortSelect query={query} basePath={basePath} />
        </div>
      </div>

      <div className="flex items-start gap-8">
        <aside
          aria-label={t("Filters")}
          className="hidden w-64 shrink-0 rounded-xl bg-card/95 p-5 shadow-sm ring-1 ring-foreground/10 lg:block"
        >
          <FiltersPanel query={query} options={options} basePath={basePath} />
        </aside>

        <div className="grid min-w-0 flex-1 gap-8">
          {page.results.length ? (
            <ul className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
              {page.results.map((variety, index) => (
                <li key={variety.id} className="flex">
                  <VarietyCard
                    variety={variety}
                    href={href(`/catalog/${variety.slug}`)}
                    locale={locale}
                    t={t}
                    preload={index < 2}
                  />
                </li>
              ))}
            </ul>
          ) : (
            <div className="flex flex-col items-center gap-4 rounded-xl border border-dashed p-12 text-center">
              <SearchXIcon className="size-10 text-muted-foreground" aria-hidden="true" />
              <p className="text-lg font-medium">{t("Nothing found")}</p>
              {hasFilters(query) && (
                <>
                  <p className="text-sm text-muted-foreground">
                    {t("Try changing the search or the filters.")}
                  </p>
                  <Button asChild variant="outline">
                    <Link href={catalogHref(basePath, resetFilters(query))}>
                      {t("Reset filters")}
                    </Link>
                  </Button>
                </>
              )}
            </div>
          )}

          <Pagination
            page={query.page}
            totalPages={totalPages}
            hrefFor={(page) => catalogHref(basePath, withPage(query, page))}
            t={t}
          />
        </div>
      </div>
    </div>
  );
}
