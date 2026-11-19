import { describe, expect, it } from "vitest";

import {
  catalogHref,
  countActiveFilters,
  emptyQuery,
  hasFilters,
  parseCatalogQuery,
  resetFilters,
  setRange,
  toSearchParams,
  toggleDictionaryValue,
  withPage,
} from "./catalog-query";

describe("parseCatalogQuery", () => {
  it("returns defaults for an empty URL", () => {
    expect(parseCatalogQuery({})).toEqual(emptyQuery());
  });

  it("reads every supported parameter", () => {
    const query = parseCatalogQuery({
      page: "3",
      letter: "р",
      search: "  аметист ",
      ordering: "-views_count",
      in_stock: "true",
      ripening: ["rannii", "duzhe-rannii", "rannii"],
      berry_color: "synii",
      bunch_weight_min: "0,5",
      frost_max: "-25",
    });

    expect(query.page).toBe(3);
    expect(query.letter).toBe("Р");
    expect(query.search).toBe("аметист");
    expect(query.ordering).toBe("-views_count");
    expect(query.inStock).toBe(true);
    expect(query.dictionaries.ripening).toEqual(["duzhe-rannii", "rannii"]);
    expect(query.dictionaries.berry_color).toEqual(["synii"]);
    expect(query.ranges.bunch_weight).toEqual({ min: 0.5 });
    expect(query.ranges.frost).toEqual({ max: -25 });
  });

  it("drops malformed values", () => {
    const query = parseCatalogQuery({
      page: "-2",
      ordering: "price",
      in_stock: "yes",
      ripening: ["Bad Slug", "<script>"],
      berry_size_min: "abc",
      letter: "",
    });
    expect(query).toEqual(emptyQuery());
  });

  it("limits the search length and keeps one letter", () => {
    const query = parseCatalogQuery({ search: "x".repeat(300), letter: "Аб" });
    expect(query.search).toHaveLength(100);
    expect(query.letter).toBe("А");
  });
});

describe("toSearchParams / catalogHref", () => {
  it("round-trips through the URL in a canonical order", () => {
    const url =
      "page=2&ordering=name&in_stock=true&frost_min=-20&taste=muskatnyi&ripening=piznii&ripening=rannii&search=a&letter=Б";
    const query = parseCatalogQuery(Object.fromEntries(groupParams(url)));

    expect(toSearchParams(query).toString()).toBe(
      "letter=%D0%91&search=a&ripening=piznii&ripening=rannii&taste=muskatnyi&frost_min=-20&in_stock=true&ordering=name&page=2",
    );
  });

  it("omits defaults and the question mark", () => {
    expect(catalogHref("/catalog", emptyQuery())).toBe("/catalog");
    expect(catalogHref("/en/catalog", withPage(emptyQuery(), 2))).toBe("/en/catalog?page=2");
  });
});

describe("query updates", () => {
  const base = withPage(parseCatalogQuery({ ripening: "rannii", ordering: "name" }), 4);

  it("toggles a dictionary value and returns to page 1", () => {
    const added = toggleDictionaryValue(base, "ripening", "duzhe-rannii");
    expect(added.dictionaries.ripening).toEqual(["duzhe-rannii", "rannii"]);
    expect(added.page).toBe(1);

    const removed = toggleDictionaryValue(added, "ripening", "rannii");
    expect(removed.dictionaries.ripening).toEqual(["duzhe-rannii"]);
    // The original query is not mutated.
    expect(base.dictionaries.ripening).toEqual(["rannii"]);
  });

  it("sets a range", () => {
    const query = setRange(base, "berry_weight", { min: 5, max: 9 });
    expect(query.ranges.berry_weight).toEqual({ min: 5, max: 9 });
    expect(query.page).toBe(1);
  });

  it("counts active filters", () => {
    let query = setRange(base, "frost", { min: -25 });
    query = { ...query, inStock: true, search: "x", letter: "А" };
    expect(countActiveFilters(query)).toBe(3);
    expect(countActiveFilters(emptyQuery())).toBe(0);
  });

  it("knows when the list is narrowed", () => {
    expect(hasFilters(emptyQuery())).toBe(false);
    expect(hasFilters({ ...emptyQuery(), search: "x" })).toBe(true);
    expect(hasFilters({ ...emptyQuery(), letter: "А" })).toBe(true);
    expect(hasFilters(base)).toBe(true);
  });

  it("resets filters but keeps the ordering", () => {
    const reset = resetFilters({ ...base, search: "x", letter: "А", inStock: true });
    expect(reset).toEqual({ ...emptyQuery(), ordering: "name" });
  });
});

/** Group a query string into the `searchParams` shape Next.js passes to pages. */
function groupParams(search: string): Map<string, string | string[]> {
  const grouped = new Map<string, string | string[]>();
  for (const [key, value] of new URLSearchParams(search)) {
    const existing = grouped.get(key);
    grouped.set(key, existing === undefined ? value : [existing, value].flat());
  }
  return grouped;
}
