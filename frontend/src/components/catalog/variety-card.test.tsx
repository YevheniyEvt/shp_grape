import { render, screen } from "@testing-library/react";
import type { ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";

import { I18nProvider } from "@/i18n/client";

import { makeVariety, t } from "./test-utils";
import { cardOffer, VarietyCard } from "./variety-card";

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }));

const plain = (text: string | null | undefined) => text?.replace(/\s/g, " ");

// The cart button is a Client Component that reads the translator from the context.
const renderCard = (card: ReactElement) =>
  render(
    <I18nProvider locale="uk" catalog={{ catalog: {}, plural: null }}>
      {card}
    </I18nProvider>,
  );

describe("VarietyCard", () => {
  it("shows the name as a link, badges, facts and the lowest price", () => {
    renderCard(
      <VarietyCard variety={makeVariety()} href="/catalog/rankovyi-ametyst" locale="uk" t={t} />,
    );

    expect(screen.getByRole("link", { name: "Ранковий Аметист" })).toHaveAttribute(
      "href",
      "/catalog/rankovyi-ametyst",
    );
    expect(screen.getByText("Ранній")).toBeInTheDocument();
    expect(screen.getByText("In stock")).toBeInTheDocument();
    expect(screen.getByText("0,5–0,8 kg")).toBeInTheDocument();
    expect(screen.getByText("8–10 g")).toBeInTheDocument();
    expect(screen.getByText("-23 °C")).toBeInTheDocument();
    expect(plain(screen.getByText(/^from/).textContent)).toBe("from 30 ₴");
    expect(screen.getByRole("img", { name: "Photo" })).toHaveAttribute("width", "1200");
    expect(screen.queryByText("Recommended")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Add to cart/ })).toBeEnabled();
  });

  it("handles a variety without photo, prices or characteristics", () => {
    const variety = makeVariety({
      main_photo: null,
      ripening: null,
      bunch_weight_min: null,
      bunch_weight_max: null,
      berry_weight_min: null,
      berry_weight_max: null,
      frost_resistance: null,
      cutting_price: null,
      sapling_price: null,
      cutting_available: false,
      is_featured: true,
    });
    renderCard(<VarietyCard variety={variety} href="/x" locale="en" t={t} />);

    expect(screen.getByTestId("photo-placeholder")).toBeInTheDocument();
    expect(screen.getByText("Out of stock")).toBeInTheDocument();
    expect(screen.getByText("Recommended")).toBeInTheDocument();
    expect(screen.queryByRole("term")).not.toBeInTheDocument();
    expect(screen.queryByText(/^from/)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Add to cart/ })).toBeDisabled();
  });
});

describe("cardOffer", () => {
  const base = {
    cutting_price: 30,
    cutting_available: true,
    sapling_price: 120,
    sapling_available: true,
  };

  it("prefers cuttings, then saplings", () => {
    expect(cardOffer(base)).toEqual({ kind: "cutting", price: 30 });
    expect(cardOffer({ ...base, cutting_available: false })).toEqual({
      kind: "sapling",
      price: 120,
    });
  });

  it("needs a price and availability", () => {
    expect(cardOffer({ ...base, cutting_price: null, sapling_available: false })).toBeNull();
    expect(cardOffer({ ...base, cutting_available: false, sapling_price: null })).toBeNull();
  });
});
