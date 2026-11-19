/**
 * Catalog state that lives in the URL (`/catalog?ripening=rannii&page=2`).
 *
 * The query-string names are the same as the API filter names, so one canonical
 * string serves both the page URL and the API request. Parsing is forgiving:
 * unknown or malformed values are dropped instead of failing the page.
 */

export const DICTIONARY_FILTERS = ["ripening", "berry_color", "pulp", "taste", "vigor"] as const;
export const RANGE_FILTERS = [
  "bunch_weight",
  "berry_weight",
  "berry_size",
  "disease",
  "frost",
] as const;
export const ORDERINGS = ["name", "ripening", "-created", "-views_count"] as const;

export type DictionaryFilter = (typeof DICTIONARY_FILTERS)[number];
export type RangeFilter = (typeof RANGE_FILTERS)[number];
export type Ordering = (typeof ORDERINGS)[number];
export type NumberRange = { min?: number; max?: number };

export type CatalogQuery = {
  page: number;
  letter?: string;
  search?: string;
  ordering?: Ordering;
  inStock: boolean;
  dictionaries: Record<DictionaryFilter, string[]>;
  ranges: Record<RangeFilter, NumberRange>;
};

/** `searchParams` of a page: every value may be missing, single or repeated. */
export type RawSearchParams = Record<string, string | string[] | undefined>;

export const CATALOG_PAGE_SIZE = 24;

const SLUG = /^[a-z0-9-]+$/;

function values(params: RawSearchParams, name: string): string[] {
  const value = params[name];
  if (value === undefined) return [];
  return (Array.isArray(value) ? value : [value]).map((item) => item.trim()).filter(Boolean);
}

function first(params: RawSearchParams, name: string): string | undefined {
  return values(params, name)[0];
}

function number(params: RawSearchParams, name: string): number | undefined {
  const raw = first(params, name);
  if (raw === undefined) return undefined;
  const parsed = Number(raw.replace(",", "."));
  return Number.isFinite(parsed) ? parsed : undefined;
}

function recordOf<K extends string, V>(keys: readonly K[], make: () => V): Record<K, V> {
  return Object.fromEntries(keys.map((key) => [key, make()])) as Record<K, V>;
}

export function emptyQuery(): CatalogQuery {
  return {
    page: 1,
    inStock: false,
    dictionaries: recordOf(DICTIONARY_FILTERS, (): string[] => []),
    ranges: recordOf(RANGE_FILTERS, (): NumberRange => ({})),
  };
}

export function parseCatalogQuery(params: RawSearchParams): CatalogQuery {
  const query = emptyQuery();

  const page = Number(first(params, "page"));
  if (Number.isInteger(page) && page > 1) query.page = page;

  const letter = first(params, "letter");
  if (letter) query.letter = Array.from(letter)[0].toUpperCase();

  const search = first(params, "search");
  if (search) query.search = search.slice(0, 100);

  const ordering = first(params, "ordering");
  if (ORDERINGS.includes(ordering as Ordering)) query.ordering = ordering as Ordering;

  query.inStock = first(params, "in_stock") === "true";

  for (const name of DICTIONARY_FILTERS) {
    const slugs = values(params, name).filter((slug) => SLUG.test(slug));
    query.dictionaries[name] = [...new Set(slugs)].sort();
  }

  for (const name of RANGE_FILTERS) {
    const min = number(params, `${name}_min`);
    const max = number(params, `${name}_max`);
    query.ranges[name] = {
      ...(min !== undefined && { min }),
      ...(max !== undefined && { max }),
    };
  }
  return query;
}

/** Canonical query string (stable order, defaults omitted) for page links and the API. */
export function toSearchParams(query: CatalogQuery): URLSearchParams {
  const params = new URLSearchParams();
  if (query.letter) params.set("letter", query.letter);
  if (query.search) params.set("search", query.search);
  for (const name of DICTIONARY_FILTERS) {
    for (const slug of query.dictionaries[name]) params.append(name, slug);
  }
  for (const name of RANGE_FILTERS) {
    const { min, max } = query.ranges[name];
    if (min !== undefined) params.set(`${name}_min`, String(min));
    if (max !== undefined) params.set(`${name}_max`, String(max));
  }
  if (query.inStock) params.set("in_stock", "true");
  if (query.ordering) params.set("ordering", query.ordering);
  if (query.page > 1) params.set("page", String(query.page));
  return params;
}

/** `basePath?query`, or just `basePath` when the query has nothing to say. */
export function catalogHref(basePath: string, query: CatalogQuery): string {
  const search = toSearchParams(query).toString();
  return search ? `${basePath}?${search}` : basePath;
}

/** A copy of the query with changes applied; any change of filters goes back to page 1. */
export function updateQuery(query: CatalogQuery, changes: Partial<CatalogQuery>): CatalogQuery {
  return { ...query, page: 1, ...changes };
}

export function withPage(query: CatalogQuery, page: number): CatalogQuery {
  return { ...query, page };
}

export function toggleDictionaryValue(
  query: CatalogQuery,
  name: DictionaryFilter,
  slug: string,
): CatalogQuery {
  const current = query.dictionaries[name];
  const next = current.includes(slug)
    ? current.filter((item) => item !== slug)
    : [...current, slug].sort();
  return updateQuery(query, { dictionaries: { ...query.dictionaries, [name]: next } });
}

export function setRange(query: CatalogQuery, name: RangeFilter, range: NumberRange): CatalogQuery {
  return updateQuery(query, { ranges: { ...query.ranges, [name]: range } });
}

/** Number of active filters shown in the panel (search, letter and ordering are separate controls). */
export function countActiveFilters(query: CatalogQuery): number {
  const dictionaries = DICTIONARY_FILTERS.reduce(
    (sum, name) => sum + query.dictionaries[name].length,
    0,
  );
  const ranges = RANGE_FILTERS.filter(
    (name) => query.ranges[name].min !== undefined || query.ranges[name].max !== undefined,
  ).length;
  return dictionaries + ranges + (query.inStock ? 1 : 0);
}

/** True when anything narrows the list (used for the "nothing found" state). */
export function hasFilters(query: CatalogQuery): boolean {
  return Boolean(query.letter || query.search) || countActiveFilters(query) > 0;
}

/** Clear every filter, the letter and the search; keep the ordering. */
export function resetFilters(query: CatalogQuery): CatalogQuery {
  return { ...emptyQuery(), ordering: query.ordering };
}
