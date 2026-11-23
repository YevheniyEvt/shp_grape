/**
 * Browser calls of the orders API: cart check, checkout, pre-order and contact forms.
 *
 * Errors are returned as values (not thrown), so forms can show them next to the fields.
 */

import type { Locale } from "@/i18n/config";
import type { CartItem, CheckedLine } from "@/lib/cart/cart";
import { fieldErrors } from "@/lib/forms";

import { apiUrl } from "./client";

export type SubmitError =
  | { kind: "validation"; fields: Record<string, string> }
  | { kind: "throttled" }
  | { kind: "network" }
  | { kind: "server" };

export type CartCheck = { items: CheckedLine[]; total: number; has_problems: boolean };

export type OrderResult =
  | { ok: true; number: string; total: number }
  | { ok: false; kind: "conflict"; detail: string; items: CheckedLine[] }
  | ({ ok: false } & SubmitError);

export type CheckoutData = {
  full_name: string;
  phone: string;
  email: string;
  city: string;
  delivery_office: string;
  contact_method: string;
  comment: string;
  website: string;
};

export type PreorderData = {
  full_name: string;
  phone: string;
  email: string;
  description: string;
  website: string;
};

export type ContactData = {
  name: string;
  email: string;
  subject: string;
  message: string;
  website: string;
};

async function post(path: string, body: unknown, locale: Locale): Promise<Response | null> {
  try {
    return await fetch(apiUrl(path), {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Accept-Language": locale,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });
  } catch {
    return null;
  }
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

async function toError(response: Response | null): Promise<SubmitError> {
  if (!response) return { kind: "network" };
  if (response.status === 429) return { kind: "throttled" };
  if (response.status === 400)
    return { kind: "validation", fields: fieldErrors(await readJson(response)) };
  return { kind: "server" };
}

const orderItems = (items: CartItem[]) =>
  items.map(({ slug, kind, quantity, price }) => ({ variety: slug, kind, quantity, price }));

/** Current data of the cart items; null when the check failed (the cart then stays as is). */
export async function checkCart(items: CartItem[], locale: Locale): Promise<CartCheck | null> {
  if (!items.length) return { items: [], total: 0, has_problems: false };
  const response = await post("/api/cart/validate/", { items: orderItems(items) }, locale);
  if (!response?.ok) return null;
  return (await readJson(response)) as CartCheck;
}

export async function placeOrder(
  data: CheckoutData,
  items: CartItem[],
  locale: Locale,
): Promise<OrderResult> {
  const response = await post("/api/orders/", { ...data, items: orderItems(items) }, locale);
  if (response?.status === 201) {
    const body = (await readJson(response)) as { number: string; total: number };
    return { ok: true, ...body };
  }
  if (response?.status === 409) {
    const body = (await readJson(response)) as { detail: string; items: CheckedLine[] };
    return { ok: false, kind: "conflict", ...body };
  }
  return { ok: false, ...(await toError(response)) };
}

async function send(path: string, data: object, locale: Locale): Promise<SubmitError | null> {
  const response = await post(path, data, locale);
  return response?.ok ? null : toError(response);
}

/** Send a pre-order; returns null on success or the error. */
export const sendPreorder = (data: PreorderData, locale: Locale) =>
  send("/api/preorders/", data, locale);

/** Send a contact form message; returns null on success or the error. */
export const sendContactMessage = (data: ContactData, locale: Locale) =>
  send("/api/contact/", data, locale);
