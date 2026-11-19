import { act, fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { I18nProvider } from "@/i18n/client";
import type { FilterOptions } from "@/lib/api/catalog";
import { parseCatalogQuery } from "@/lib/catalog-query";

import { CatalogSearch, SEARCH_DELAY } from "./catalog-search";
import { FiltersPanel, sliderToRange } from "./filters-panel";

const router = { push: vi.fn(), replace: vi.fn() };
vi.mock("next/navigation", () => ({ useRouter: () => router }));

function wrap(children: ReactNode) {
  return (
    <I18nProvider locale="uk" catalog={{ catalog: {}, plural: null }}>
      {children}
    </I18nProvider>
  );
}

const options: FilterOptions = {
  ripening: [
    { slug: "rannii", name: "Ранній" },
    { slug: "piznii", name: "Пізній" },
  ],
  berry_color: [],
  pulp: [],
  taste: [],
  vigor: [],
  ranges: {
    bunch_weight: { min: 0.3, max: 1.2 },
    berry_weight: { min: null, max: null },
    berry_size: { min: 18, max: 18 },
    disease: { min: 2, max: 4 },
    frost: { min: -26, max: -20 },
  },
};

beforeEach(() => {
  router.push.mockReset();
  router.replace.mockReset();
});

describe("sliderToRange", () => {
  const bounds = { min: 0, max: 10 };

  it("drops bounds left at the edges", () => {
    expect(sliderToRange([0, 10], bounds)).toEqual({});
    expect(sliderToRange([2, 10], bounds)).toEqual({ min: 2 });
    expect(sliderToRange([0, 7], bounds)).toEqual({ max: 7 });
    expect(sliderToRange([2, 7], bounds)).toEqual({ min: 2, max: 7 });
  });
});

describe("FiltersPanel", () => {
  it("shows dictionaries with values and usable ranges only", () => {
    render(
      wrap(<FiltersPanel query={parseCatalogQuery({})} options={options} basePath="/catalog" />),
    );

    expect(screen.getByRole("group", { name: "Ripening period" })).toBeInTheDocument();
    expect(screen.queryByRole("group", { name: "Berry colour" })).not.toBeInTheDocument();
    // bunch weight, disease and frost: two thumbs each; empty and one-value ranges are hidden.
    expect(screen.getAllByRole("slider")).toHaveLength(6);
    expect(screen.getByRole("button", { name: "Reset filters" })).toBeDisabled();
  });

  it("toggles a dictionary value through the URL", () => {
    const query = parseCatalogQuery({ page: "3", ordering: "name" });
    render(wrap(<FiltersPanel query={query} options={options} basePath="/en/catalog" />));

    fireEvent.click(screen.getByRole("checkbox", { name: "Пізній" }));

    expect(router.push).toHaveBeenCalledWith("/en/catalog?ripening=piznii&ordering=name", {
      scroll: false,
    });
  });

  it("filters by stock and resets everything but the ordering", () => {
    const query = parseCatalogQuery({ ripening: "rannii", ordering: "-created", letter: "А" });
    render(wrap(<FiltersPanel query={query} options={options} basePath="/catalog" />));

    expect(screen.getByRole("checkbox", { name: "Ранній" })).toBeChecked();
    fireEvent.click(screen.getByRole("checkbox", { name: "In stock only" }));
    expect(router.push).toHaveBeenLastCalledWith(
      "/catalog?letter=%D0%90&ripening=rannii&in_stock=true&ordering=-created",
      { scroll: false },
    );

    fireEvent.click(screen.getByRole("button", { name: "Reset filters" }));
    expect(router.push).toHaveBeenLastCalledWith("/catalog?ordering=-created", { scroll: false });
  });
});

describe("CatalogSearch", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("updates the URL after the visitor stops typing", () => {
    const query = parseCatalogQuery({ page: "2", ripening: "rannii" });
    render(wrap(<CatalogSearch query={query} basePath="/catalog" />));
    const input = screen.getByRole("searchbox", { name: "Search by name" });

    fireEvent.change(input, { target: { value: "аме" } });
    act(() => vi.advanceTimersByTime(SEARCH_DELAY - 100));
    expect(router.replace).not.toHaveBeenCalled();

    fireEvent.change(input, { target: { value: "аметист " } });
    act(() => vi.advanceTimersByTime(SEARCH_DELAY));
    expect(router.replace).toHaveBeenCalledTimes(1);
    expect(router.replace).toHaveBeenCalledWith(
      `/catalog?search=${encodeURIComponent("аметист")}&ripening=rannii`,
      { scroll: false },
    );
  });

  it("follows the URL when it changes from outside", () => {
    const { rerender } = render(
      wrap(<CatalogSearch query={parseCatalogQuery({ search: "abc" })} basePath="/catalog" />),
    );
    const input = screen.getByRole("searchbox");
    expect(input).toHaveValue("abc");

    rerender(wrap(<CatalogSearch query={parseCatalogQuery({})} basePath="/catalog" />));
    expect(input).toHaveValue("");
    act(() => vi.advanceTimersByTime(SEARCH_DELAY * 2));
    expect(router.replace).not.toHaveBeenCalled();
  });

  it("clears the search with the button", () => {
    render(
      wrap(<CatalogSearch query={parseCatalogQuery({ search: "abc" })} basePath="/catalog" />),
    );
    fireEvent.click(screen.getByRole("button", { name: "Clear search" }));
    act(() => vi.advanceTimersByTime(SEARCH_DELAY));
    expect(router.replace).toHaveBeenCalledWith("/catalog", { scroll: false });
  });
});
