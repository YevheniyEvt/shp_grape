import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AlphabetBar } from "./alphabet-bar";

const hrefFor = (letter: string) => `/catalog?letter=${letter}`;

describe("AlphabetBar", () => {
  it("links available letters, mutes the rest and marks the active one", () => {
    render(
      <AlphabetBar
        letters={["А", "Б", "В"]}
        available={["А", "В"]}
        active="В"
        hrefFor={hrefFor}
        label="Letters"
      />,
    );

    expect(screen.getByRole("navigation", { name: "Letters" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "А" })).toHaveAttribute("href", "/catalog?letter=А");
    expect(screen.queryByRole("link", { name: "Б" })).not.toBeInTheDocument();
    expect(screen.getByText("Б")).toHaveAttribute("aria-disabled", "true");
    expect(screen.getByRole("link", { name: "В" })).toHaveAttribute("aria-current", "true");
  });

  it("links every letter when availability is unknown", () => {
    render(<AlphabetBar letters={["A", "B"]} available={null} hrefFor={hrefFor} label="L" />);
    expect(screen.getAllByRole("link")).toHaveLength(2);
  });
});
