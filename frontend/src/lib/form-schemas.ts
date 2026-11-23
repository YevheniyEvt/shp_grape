/**
 * Zod schemas of the site forms. Built from the translator, so messages follow the site language;
 * the server repeats every check, these only give fast feedback.
 */

import { z } from "zod";

import type { Translator } from "@/i18n/gettext";

import { isCompletePhone } from "./forms";

type T = Translator["t"];

export const CONTACT_METHODS = ["phone", "viber", "telegram", "email"] as const;

const required = (t: T, max: number) =>
  z
    .string()
    .trim()
    .min(1, { error: t("This field is required.") })
    .max(max, { error: t("Too long.") });

const optional = (t: T, max: number) =>
  z
    .string()
    .trim()
    .max(max, { error: t("Too long.") });

const phone = (t: T) =>
  z.string().refine(isCompletePhone, { error: t("Enter the full phone number.") });

const optionalEmail = (t: T) =>
  z.union([z.literal(""), z.email({ error: t("Enter a valid email address.") })]);

export function checkoutSchema(t: T) {
  return z.object({
    full_name: required(t, 200),
    phone: phone(t),
    email: optionalEmail(t),
    city: optional(t, 100),
    delivery_office: optional(t, 200),
    contact_method: z.enum(CONTACT_METHODS),
    comment: optional(t, 2000),
    website: z.string(),
  });
}

export function preorderSchema(t: T) {
  return z.object({
    full_name: required(t, 200),
    phone: phone(t),
    email: optionalEmail(t),
    description: required(t, 2000),
    website: z.string(),
  });
}

export function contactSchema(t: T) {
  return z.object({
    name: required(t, 200),
    email: z.email({ error: t("Enter a valid email address.") }),
    subject: optional(t, 200),
    message: required(t, 5000),
    website: z.string(),
  });
}

export type CheckoutValues = z.infer<ReturnType<typeof checkoutSchema>>;
export type PreorderValues = z.infer<ReturnType<typeof preorderSchema>>;
export type ContactValues = z.infer<ReturnType<typeof contactSchema>>;
