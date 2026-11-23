import { describe, expect, it } from "vitest";

import {
  addItem,
  applyCheck,
  cartCount,
  cartTotal,
  clampQuantity,
  itemKey,
  removeItem,
  setQuantity,
  type CartItem,
  type CheckedLine,
} from "./cart";

const cutting: CartItem = {
  slug: "rubin",
  kind: "cutting",
  quantity: 2,
  price: 30,
  name: "Рубін",
  image: null,
};
const sapling: CartItem = { ...cutting, kind: "sapling", quantity: 1, price: 120 };

function line(overrides: Partial<CheckedLine>): CheckedLine {
  return {
    variety: "rubin",
    kind: "cutting",
    quantity: 2,
    name: "Рубін",
    price: 30,
    available: true,
    problem: null,
    photo: null,
    ...overrides,
  };
}

describe("cart items", () => {
  it("clamps quantities", () => {
    expect(clampQuantity(0)).toBe(1);
    expect(clampQuantity(3.6)).toBe(4);
    expect(clampQuantity(500)).toBe(99);
    expect(clampQuantity(Number.NaN)).toBe(1);
  });

  it("adds new items and sums repeated ones", () => {
    let items = addItem([], cutting);
    items = addItem(items, sapling);
    items = addItem(items, { ...cutting, quantity: 3, price: 35 });
    expect(items).toEqual([{ ...cutting, quantity: 5, price: 35 }, sapling]);
    expect(addItem(items, { ...cutting, quantity: 200 })[0].quantity).toBe(99);
    expect(addItem([], { ...cutting, quantity: 0 })[0].quantity).toBe(1);
  });

  it("changes quantities and removes items", () => {
    const items = [cutting, sapling];
    expect(setQuantity(items, sapling, 4)).toEqual([cutting, { ...sapling, quantity: 4 }]);
    expect(setQuantity(items, sapling, -1)[1].quantity).toBe(1);
    expect(removeItem(items, cutting)).toEqual([sapling]);
  });

  it("counts items and the total", () => {
    expect(cartCount([cutting, sapling])).toBe(3);
    expect(cartTotal([cutting, sapling])).toBe(180);
    expect(cartTotal([])).toBe(0);
    expect(itemKey(cutting)).toBe("rubin:cutting");
  });
});

describe("applyCheck", () => {
  it("updates names, prices and photos and reports problems", () => {
    const { items, problems } = applyCheck(
      [cutting, sapling, { ...cutting, slug: "gone" }],
      [
        line({ name: "Ruby", photo: { thumb: "http://api/t.webp" } }),
        line({ kind: "sapling", price: 140, problem: "price_changed" }),
        line({ variety: "gone", name: null, price: null, problem: "not_found" }),
      ],
    );
    expect(items).toEqual([
      { ...cutting, name: "Ruby", image: "http://api/t.webp" },
      { ...sapling, price: 140 },
    ]);
    expect(problems).toEqual({ "rubin:sapling": "price_changed", "gone:cutting": "not_found" });
  });

  it("keeps unavailable items and items the server did not return", () => {
    const { items, problems } = applyCheck(
      [cutting, sapling],
      [line({ kind: "sapling", available: false, problem: "unavailable", price: null })],
    );
    expect(items).toEqual([cutting, sapling]);
    expect(problems).toEqual({ "rubin:sapling": "unavailable" });
  });
});
