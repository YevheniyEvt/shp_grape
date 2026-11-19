import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { t } from "@/components/catalog/test-utils";
import { catalogHref, parseCatalogQuery, withPage } from "@/lib/catalog-query";

import { pageItems, Pagination } from "./pagination";

describe("pageItems", () => {
  it.each([
    [1, 1, [1]],
    [1, 3, [1, 2, 3]],
    [1, 10, [1, 2, "gap", 10]],
    [5, 10, [1, "gap", 4, 5, 6, "gap", 10]],
    [3, 10, [1, 2, 3, 4, "gap", 10]],
    [10, 10, [1, "gap", 9, 10]],
  ])("page %i of %i", (current, total, expected) => {
    expect(pageItems(current, total)).toEqual(expected);
  });
});

describe("Pagination", () => {
  it("renders nothing for a single page", () => {
    const { container } = render(<Pagination page={1} totalPages={1} hrefFor={String} t={t} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("links pages keeping the filters", () => {
    const query = parseCatalogQuery({ page: "2", ripening: "rannii" });
    render(
      <Pagination
        page={query.page}
        totalPages={3}
        hrefFor={(page) => catalogHref("/en/catalog", withPage(query, page))}
        t={t}
      />,
    );

    expect(screen.getByText("2")).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "1" })).toHaveAttribute(
      "href",
      "/en/catalog?ripening=rannii",
    );
    expect(screen.getByRole("link", { name: /Next/ })).toHaveAttribute(
      "href",
      "/en/catalog?ripening=rannii&page=3",
    );
    expect(screen.getByRole("link", { name: /Previous/ })).toHaveAttribute("rel", "prev");
  });

  it("clamps a page past the end", () => {
    render(<Pagination page={9} totalPages={2} hrefFor={(page) => `/c?page=${page}`} t={t} />);
    expect(screen.getByText("2")).toHaveAttribute("aria-current", "page");
    expect(screen.queryByRole("link", { name: /Next/ })).not.toBeInTheDocument();
  });
});
