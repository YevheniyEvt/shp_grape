import { fireEvent, render, screen, within } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { makePhoto, makeVarietyDetail, t } from "@/components/catalog/test-utils";
import { I18nProvider } from "@/i18n/client";

import { buildCharacteristics, CharacteristicsTable } from "./characteristics";
import { clampQuantity, PriceBlock } from "./price-block";
import { VarietyGallery } from "./variety-gallery";
import { viewedKey, ViewCounter } from "./view-counter";

const registerView = vi.fn();
vi.mock("@/lib/api/views", () => ({ registerView: (slug: string) => registerView(slug) }));

function wrap(children: ReactNode) {
  return (
    <I18nProvider locale="uk" catalog={{ catalog: {}, plural: null }}>
      {children}
    </I18nProvider>
  );
}

const plain = (text: string | null | undefined) => text?.replace(/\s/g, " ");

describe("buildCharacteristics", () => {
  it("lists filled characteristics with units", () => {
    const rows = buildCharacteristics(makeVarietyDetail({ alt_names: "Аметист" }), t, "uk");
    const byLabel = Object.fromEntries(rows.map((row) => [row.label, row.value]));

    expect(byLabel).toMatchObject({
      Breeder: "О. Демченко",
      "Ripening period": "Ранній",
      Pulp: "Хрустка",
      "Bunch weight": "0,5–0,8 kg",
      "Berry size": "24–28 mm",
      "Disease susceptibility": "2,5–3 points",
      "Frost resistance": "down to -23 °C",
      "Also known as": "Аметист",
    });
    expect(byLabel).not.toHaveProperty("Growth vigour");
  });

  it("skips every empty value", () => {
    const rows = buildCharacteristics(
      makeVarietyDetail({
        author: "",
        ripening: null,
        berry_color: null,
        pulp: null,
        taste: null,
        bunch_weight_min: null,
        bunch_weight_max: null,
        berry_weight_min: null,
        berry_weight_max: null,
        berry_size_min: null,
        berry_size_max: null,
        disease_susceptibility_min: null,
        disease_susceptibility_max: null,
        frost_resistance: null,
      }),
      t,
      "en",
    );
    expect(rows).toEqual([]);
  });

  it("renders a table, or nothing without rows", () => {
    const { container, rerender } = render(
      <CharacteristicsTable rows={[{ label: "Taste", value: "Muscat" }]} caption="Specs" />,
    );
    expect(screen.getByRole("rowheader", { name: "Taste" })).toBeInTheDocument();
    rerender(<CharacteristicsTable rows={[]} caption="Specs" />);
    expect(container).toBeEmptyDOMElement();
  });
});

describe("PriceBlock", () => {
  it("clamps the quantity", () => {
    expect(clampQuantity(0)).toBe(1);
    expect(clampQuantity(3.6)).toBe(4);
    expect(clampQuantity(500)).toBe(99);
    expect(clampQuantity(Number.NaN)).toBe(1);
  });

  it("selects an available offer and multiplies the price", () => {
    render(
      wrap(
        <PriceBlock
          offers={[
            { kind: "cutting", price: 30, available: false },
            { kind: "sapling", price: 120, available: true },
          ]}
        />,
      ),
    );

    expect(screen.getByRole("radio", { name: /Cutting/ })).toBeDisabled();
    expect(screen.getByRole("radio", { name: /Sapling/ })).toHaveAttribute("aria-checked", "true");

    fireEvent.click(screen.getByRole("button", { name: "Increase quantity" }));
    fireEvent.click(screen.getByRole("button", { name: "Increase quantity" }));
    expect(screen.getByRole("spinbutton", { name: "Quantity" })).toHaveValue(3);
    expect(plain(screen.getByTestId("total").textContent)).toBe("360 ₴");

    fireEvent.change(screen.getByRole("spinbutton"), { target: { value: "1000" } });
    expect(screen.getByRole("spinbutton")).toHaveValue(99);
    fireEvent.click(screen.getByRole("button", { name: "Decrease quantity" }));
    expect(screen.getByRole("spinbutton")).toHaveValue(98);
  });

  it("explains when nothing can be ordered", () => {
    render(
      wrap(
        <PriceBlock
          offers={[
            { kind: "cutting", price: 30, available: false },
            { kind: "sapling", price: null, available: true },
          ]}
        />,
      ),
    );
    expect(screen.getByText("This variety is not available now.")).toBeInTheDocument();
    expect(screen.queryByRole("spinbutton")).not.toBeInTheDocument();
  });
});

describe("VarietyGallery", () => {
  it("shows a placeholder without photos", () => {
    render(wrap(<VarietyGallery photos={[]} name="X" />));
    expect(screen.getByTestId("photo-placeholder")).toBeInTheDocument();
  });

  it("switches the large photo and opens the lightbox", () => {
    const photos = [
      makePhoto({ id: 1, alt: "First", medium: "http://api/1.webp" }),
      makePhoto({ id: 2, alt: "Second", medium: "http://api/2.webp" }),
    ];
    render(wrap(<VarietyGallery photos={photos} name="Аметист" />));

    const main = screen.getByRole("button", { name: "Open photo 1 of 2" });
    expect(within(main).getByRole("img")).toHaveAttribute("src", "http://api/1.webp");

    fireEvent.click(screen.getByRole("button", { name: "Show photo 2" }));
    const switched = screen.getByRole("button", { name: "Open photo 2 of 2" });
    expect(within(switched).getByRole("img")).toHaveAttribute("src", "http://api/2.webp");

    fireEvent.click(switched);
    expect(screen.getByRole("button", { name: "Close" })).toBeInTheDocument();
  });
});

describe("ViewCounter", () => {
  beforeEach(() => {
    registerView.mockReset();
    sessionStorage.clear();
  });

  it("counts a view once per session", () => {
    const { unmount } = render(<ViewCounter slug="rankovyi-ametyst" />);
    unmount();
    render(<ViewCounter slug="rankovyi-ametyst" />);

    expect(registerView).toHaveBeenCalledTimes(1);
    expect(registerView).toHaveBeenCalledWith("rankovyi-ametyst");
    expect(sessionStorage.getItem(viewedKey("rankovyi-ametyst"))).toBe("1");
  });

  it("still counts when storage is blocked", () => {
    const getItem = vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    render(<ViewCounter slug="x" />);
    expect(registerView).toHaveBeenCalledWith("x");
    getItem.mockRestore();
  });
});
