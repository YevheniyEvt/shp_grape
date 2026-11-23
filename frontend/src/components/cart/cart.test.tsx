import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { I18nProvider } from "@/i18n/client";
import type { CartItem, CheckedLine } from "@/lib/cart/cart";
import { useCart } from "@/lib/cart/store";

import { AddToCartButton } from "./add-to-cart-button";
import { CartCount } from "./cart-count";
import { CartHydration } from "./cart-hydration";
import { CartView } from "./cart-view";
import { CheckoutForm } from "./checkout-form";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));

const toastSuccess = vi.fn();
vi.mock("sonner", () => ({ toast: { success: (...args: unknown[]) => toastSuccess(...args) } }));

const checkCart = vi.fn();
const placeOrder = vi.fn();
vi.mock("@/lib/api/orders", () => ({
  checkCart: (...args: unknown[]) => checkCart(...args),
  placeOrder: (...args: unknown[]) => placeOrder(...args),
}));

const wrap = (children: ReactNode) => (
  <I18nProvider locale="uk" catalog={{ catalog: {}, plural: null }}>
    {children}
  </I18nProvider>
);

const rubin: CartItem = {
  slug: "rubin",
  kind: "cutting",
  quantity: 2,
  price: 30,
  name: "Рубін",
  image: null,
};
const sapfir: CartItem = {
  ...rubin,
  slug: "sapfir",
  name: "Сапфір",
  kind: "sapling",
  quantity: 1,
  price: 120,
};

const ok = (item: CartItem, overrides: Partial<CheckedLine> = {}): CheckedLine => ({
  variety: item.slug,
  kind: item.kind,
  quantity: item.quantity,
  name: item.name,
  price: item.price,
  available: true,
  problem: null,
  photo: null,
  ...overrides,
});

const plain = (text: string | null | undefined) => text?.replace(/\s/g, " ");

async function loadCart(items: CartItem[]) {
  localStorage.clear();
  useCart.setState({ items });
  await act(() => useCart.persist.rehydrate());
}

beforeEach(async () => {
  vi.clearAllMocks();
  checkCart.mockImplementation(async (items: CartItem[]) => ({
    items: items.map((item) => ok(item)),
    total: 0,
    has_problems: false,
  }));
  await loadCart([]);
});

describe("cart store and header", () => {
  it("adds an item with a toast and shows the count", async () => {
    render(
      wrap(
        <>
          <CartCount />
          <AddToCartButton
            product={{ slug: "rubin", name: "Рубін", image: null }}
            kind="sapling"
            price={120}
            quantity={3}
          />
        </>,
      ),
    );
    expect(screen.queryByTestId("cart-count")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Add to cart/ }));

    expect(screen.getByTestId("cart-count")).toHaveTextContent("3");
    expect(useCart.getState().items).toEqual([
      { slug: "rubin", name: "Рубін", image: null, kind: "sapling", price: 120, quantity: 3 },
    ]);
    const [title, options] = toastSuccess.mock.calls[0];
    expect(title).toBe("Added to cart");
    expect(options.description).toBe("Рубін — sapling × 3");
    options.action.onClick();
    expect(push).toHaveBeenCalledWith("/cart");
  });

  it("caps a large count", async () => {
    await loadCart([
      { ...rubin, quantity: 99 },
      { ...sapfir, quantity: 5 },
    ]);
    render(wrap(<CartCount />));
    expect(screen.getByTestId("cart-count")).toHaveTextContent("99+");
  });

  it("loads the saved cart and follows other tabs", async () => {
    localStorage.setItem(
      "vineyard-cart",
      JSON.stringify({ state: { items: [rubin] }, version: 1 }),
    );
    render(wrap(<CartHydration />));
    await waitFor(() => expect(useCart.getState().items).toEqual([rubin]));

    localStorage.setItem(
      "vineyard-cart",
      JSON.stringify({ state: { items: [rubin, sapfir] }, version: 1 }),
    );
    act(() => {
      window.dispatchEvent(new StorageEvent("storage", { key: "vineyard-cart" }));
    });
    await waitFor(() => expect(useCart.getState().items).toHaveLength(2));
  });
});

describe("CartView", () => {
  it("shows an empty cart", async () => {
    render(wrap(<CartView />));
    expect(await screen.findByText("Your cart is empty.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Go to the catalog" })).toHaveAttribute(
      "href",
      "/catalog",
    );
  });

  it("lists items, changes quantities and totals", async () => {
    await loadCart([rubin, sapfir]);
    render(wrap(<CartView />));

    expect(screen.getByRole("link", { name: "Рубін" })).toHaveAttribute("href", "/catalog/rubin");
    expect(plain(screen.getByTestId("cart-total").textContent)).toBe("180 ₴");

    fireEvent.click(screen.getAllByRole("button", { name: "Increase quantity" })[0]);
    expect(plain(screen.getByTestId("cart-total").textContent)).toBe("210 ₴");

    fireEvent.click(screen.getByRole("button", { name: "Remove Сапфір" }));
    expect(plain(screen.getByTestId("cart-total").textContent)).toBe("90 ₴");
    expect(screen.getByRole("link", { name: /Checkout/ })).toHaveAttribute("href", "/checkout");

    fireEvent.click(screen.getByRole("button", { name: /Clear the cart/ }));
    expect(screen.getByText("Your cart is empty.")).toBeInTheDocument();
    await waitFor(() => expect(checkCart).toHaveBeenCalledTimes(1));
  });

  it("applies the server check: new prices, unavailable and removed items", async () => {
    const gone = { ...rubin, slug: "gone", name: "Зниклий" };
    await loadCart([rubin, sapfir, gone]);
    checkCart.mockResolvedValue({
      items: [
        ok(rubin, { price: 35, problem: "price_changed" }),
        ok(sapfir, { available: false, problem: "unavailable" }),
        ok(gone, { name: null, price: null, problem: "not_found" }),
      ],
      total: 70,
      has_problems: true,
    });
    render(wrap(<CartView />));

    const notices = await screen.findByTestId("cart-notices");
    expect(notices).toHaveTextContent("1 item is no longer sold and was removed from the cart.");
    expect(notices).toHaveTextContent("Prices of some items have changed.");
    expect(notices).toHaveTextContent("Some items are out of stock now.");
    expect(screen.queryByText("Зниклий")).not.toBeInTheDocument();
    expect(screen.getByText("Out of stock")).toBeInTheDocument();
    // Only orderable items count; checkout waits until the unavailable item is removed.
    expect(plain(screen.getByTestId("cart-total").textContent)).toBe("70 ₴");
    expect(screen.getByRole("button", { name: "Checkout" })).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Remove Сапфір" }));
    expect(screen.getByRole("link", { name: /Checkout/ })).toBeInTheDocument();
  });

  it("keeps the cart when the check fails", async () => {
    await loadCart([rubin]);
    checkCart.mockResolvedValue(null);
    render(wrap(<CartView />));
    await waitFor(() => expect(checkCart).toHaveBeenCalled());
    expect(screen.getByText("Рубін")).toBeInTheDocument();
    expect(screen.queryByTestId("cart-notices")).not.toBeInTheDocument();
  });
});

describe("CheckoutForm", () => {
  async function fillForm() {
    const user = userEvent.setup();
    await user.type(screen.getByLabelText(/Full name/), "Іван Тестовий");
    await user.type(screen.getByRole("textbox", { name: /^Phone/ }), "0501234567");
    await user.click(screen.getByLabelText("Viber"));
    return user;
  }

  it("shows an empty cart", async () => {
    render(wrap(<CheckoutForm />));
    expect(await screen.findByText("Your cart is empty.")).toBeInTheDocument();
  });

  it("validates the fields before sending", async () => {
    await loadCart([rubin]);
    render(wrap(<CheckoutForm />));
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /Place the order/ }));

    expect(await screen.findByText("This field is required.")).toBeInTheDocument();
    expect(screen.getByText("Enter the full phone number.")).toBeInTheDocument();
    expect(screen.getByLabelText(/Full name/)).toHaveAttribute("aria-invalid", "true");
    expect(placeOrder).not.toHaveBeenCalled();
  });

  it("places the order, clears the cart and opens the confirmation", async () => {
    await loadCart([rubin]);
    placeOrder.mockResolvedValue({ ok: true, number: "261123-4821", total: 60 });
    render(wrap(<CheckoutForm />));
    expect(plain(screen.getByTestId("checkout-total").textContent)).toBe("60 ₴");

    const user = await fillForm();
    expect(screen.getByRole("textbox", { name: /^Phone/ })).toHaveValue("+380 (50) 123-45-67");
    await user.click(screen.getByRole("button", { name: /Place the order/ }));

    await waitFor(() => expect(push).toHaveBeenCalledWith("/order/success/261123-4821"));
    const [values, items, locale] = placeOrder.mock.calls[0];
    expect(values).toMatchObject({
      full_name: "Іван Тестовий",
      phone: "+380 (50) 123-45-67",
      contact_method: "viber",
      website: "",
    });
    expect(items).toEqual([rubin]);
    expect(locale).toBe("uk");
    expect(useCart.getState().items).toEqual([]);
    expect(screen.getByRole("status")).toHaveTextContent("The order is placed.");
  });

  it("updates the cart when items changed on the server", async () => {
    await loadCart([rubin]);
    placeOrder.mockResolvedValue({
      ok: false,
      kind: "conflict",
      detail: "Some items in your cart have changed.",
      items: [ok(rubin, { available: false, problem: "unavailable" })],
    });
    render(wrap(<CheckoutForm />));
    const user = await fillForm();
    await user.click(screen.getByRole("button", { name: /Place the order/ }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Some items in your cart have changed.",
    );
    expect(screen.getByRole("link", { name: "Go to cart" })).toHaveAttribute("href", "/cart");
    expect(screen.getByRole("button", { name: /Place the order/ })).toBeDisabled();
  });

  it("shows server field errors and other failures", async () => {
    await loadCart([rubin]);
    placeOrder.mockResolvedValueOnce({
      ok: false,
      kind: "validation",
      fields: { email: "Server says no.", items: "ignored" },
    });
    placeOrder.mockResolvedValueOnce({ ok: false, kind: "throttled" });
    render(wrap(<CheckoutForm />));
    const user = await fillForm();
    await user.click(screen.getByRole("button", { name: /Place the order/ }));

    expect(await screen.findByText("Server says no.")).toBeInTheDocument();
    expect(screen.getByText("Please correct the highlighted fields.")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Place the order/ }));
    expect(await screen.findByText(/Too many requests/)).toBeInTheDocument();
  });
});
