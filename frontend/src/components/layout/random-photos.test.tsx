import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { makePhoto } from "@/components/catalog/test-utils";

import { loadRandomPhotos, RandomPhotos } from "./random-photos";

const getRandomPhotos = vi.fn();
vi.mock("@/lib/api/catalog", () => ({
  getRandomPhotos: (...args: unknown[]) => getRandomPhotos(...args),
}));

const photo = {
  ...makePhoto({ alt: "Bunch" }),
  variety: { slug: "bilyi-tuman", name: "Білий Туман" },
};

describe("RandomPhotos", () => {
  it("links each thumbnail to its variety in the active locale", () => {
    render(<RandomPhotos photos={[photo]} locale="en" title="From our vineyard" />);

    expect(screen.getByRole("region", { name: "From our vineyard" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Bunch" })).toHaveAttribute(
      "href",
      "/en/catalog/bilyi-tuman",
    );
  });

  it("renders nothing without photos", () => {
    const { container } = render(<RandomPhotos photos={[]} locale="uk" title="x" />);
    expect(container).toBeEmptyDOMElement();
  });

  it("loads photos and survives an API failure", async () => {
    getRandomPhotos.mockResolvedValueOnce([photo]);
    await expect(loadRandomPhotos("uk")).resolves.toEqual([photo]);
    expect(getRandomPhotos).toHaveBeenCalledWith("uk", 8);

    getRandomPhotos.mockRejectedValueOnce(new Error("down"));
    await expect(loadRandomPhotos("uk")).resolves.toEqual([]);
  });
});
