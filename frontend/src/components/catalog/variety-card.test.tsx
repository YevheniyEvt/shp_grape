import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { makeVariety, t } from "./test-utils";
import { VarietyCard } from "./variety-card";

const plain = (text: string | null | undefined) => text?.replace(/\s/g, " ");

describe("VarietyCard", () => {
  it("shows the name as a link, badges, facts and the lowest price", () => {
    render(
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
    expect(screen.getByRole("button", { name: /Add to cart/ })).toBeDisabled();
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
    render(<VarietyCard variety={variety} href="/x" locale="en" t={t} />);

    expect(screen.getByTestId("photo-placeholder")).toBeInTheDocument();
    expect(screen.getByText("Out of stock")).toBeInTheDocument();
    expect(screen.getByText("Recommended")).toBeInTheDocument();
    expect(screen.queryByRole("term")).not.toBeInTheDocument();
    expect(screen.queryByText(/^from/)).not.toBeInTheDocument();
  });
});
