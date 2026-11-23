import { afterEach, describe, expect, it, vi } from "vitest";

import type { CartItem } from "@/lib/cart/cart";

import { checkCart, placeOrder, sendContactMessage, sendPreorder } from "./orders";

const item: CartItem = {
  slug: "rubin",
  kind: "cutting",
  quantity: 2,
  price: 30,
  name: "Рубін",
  image: null,
};

const checkout = {
  full_name: "Іван",
  phone: "+380 (50) 123-45-67",
  email: "",
  city: "",
  delivery_office: "",
  contact_method: "phone",
  comment: "",
  website: "",
};

function mockFetch(status: number, body?: unknown) {
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(body === undefined ? null : JSON.stringify(body), {
      status,
      headers: body === undefined ? {} : { "Content-Type": "application/json" },
    }),
  );
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("orders API", () => {
  it("checks the cart with the language and the shown prices", async () => {
    const fetchMock = mockFetch(200, { items: [], total: 60, has_problems: false });
    expect(await checkCart([item], "en")).toEqual({ items: [], total: 60, has_problems: false });

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://127.0.0.1:8000/api/cart/validate/");
    expect(init.method).toBe("POST");
    expect(init.headers["Accept-Language"]).toBe("en");
    expect(JSON.parse(init.body)).toEqual({
      items: [{ variety: "rubin", kind: "cutting", quantity: 2, price: 30 }],
    });
  });

  it("does not call the API for an empty cart and survives failures", async () => {
    const fetchMock = mockFetch(500);
    expect(await checkCart([], "uk")).toEqual({ items: [], total: 0, has_problems: false });
    expect(fetchMock).not.toHaveBeenCalled();
    expect(await checkCart([item], "uk")).toBeNull();
  });

  it("returns the order number", async () => {
    const fetchMock = mockFetch(201, { number: "261123-4821", total: 60 });
    expect(await placeOrder(checkout, [item], "uk")).toEqual({
      ok: true,
      number: "261123-4821",
      total: 60,
    });
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toMatchObject({
      full_name: "Іван",
      items: [{ variety: "rubin", quantity: 2 }],
    });
  });

  it("returns changed items on a conflict", async () => {
    mockFetch(409, { detail: "Changed", items: [{ variety: "rubin" }] });
    expect(await placeOrder(checkout, [item], "uk")).toEqual({
      ok: false,
      kind: "conflict",
      detail: "Changed",
      items: [{ variety: "rubin" }],
    });
  });

  it.each([
    [400, { phone: ["Bad"] }, { kind: "validation", fields: { phone: "Bad" } }],
    [429, { detail: "Slow down" }, { kind: "throttled" }],
    [500, undefined, { kind: "server" }],
  ])("maps HTTP %s", async (status, body, expected) => {
    mockFetch(status, body);
    expect(await placeOrder(checkout, [item], "uk")).toEqual({ ok: false, ...expected });
    mockFetch(status, body);
    expect(await sendPreorder({ ...checkout, description: "x" }, "uk")).toEqual(expected);
  });

  it("reports a validation error with an unreadable body", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("oops", { status: 400 })));
    expect(await sendPreorder({ ...checkout, description: "x" }, "uk")).toEqual({
      kind: "validation",
      fields: {},
    });
  });

  it("reports network errors", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));
    expect(await placeOrder(checkout, [item], "uk")).toEqual({ ok: false, kind: "network" });
    expect(
      await sendContactMessage(
        { name: "a", email: "a@b.c", subject: "", message: "m", website: "" },
        "uk",
      ),
    ).toEqual({ kind: "network" });
  });

  it("returns null when a form is sent", async () => {
    const fetchMock = mockFetch(201);
    expect(
      await sendContactMessage(
        { name: "a", email: "a@b.c", subject: "", message: "m", website: "" },
        "en",
      ),
    ).toBeNull();
    expect(fetchMock.mock.calls[0][0]).toBe("http://127.0.0.1:8000/api/contact/");
  });
});
