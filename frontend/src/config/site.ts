/**
 * Static site data used until `SiteSettings` arrives from the API (stage 5).
 * Placeholder contacts only: real data is entered in the admin later.
 */

import type { Translator } from "@/i18n/gettext";

export const siteContacts = {
  phones: ["+380 (00) 000-00-00", "+380 (00) 000-00-01"],
  email: "info@example.com",
};

/** `tel:` URI from a human-formatted phone number. */
export function phoneHref(phone: string): string {
  return `tel:${phone.replace(/[^\d+]/g, "")}`;
}

export type NavItem = { href: string; label: string };

/** Main menu. Labels go through the translator here so the string extractor finds them. */
export function getMainNav({ t }: Pick<Translator, "t">): NavItem[] {
  return [
    { href: "/", label: t("Home") },
    { href: "/catalog", label: t("Catalog") },
    { href: "/articles", label: t("Articles") },
    { href: "/news", label: t("News") },
    { href: "/gallery", label: t("Gallery") },
    { href: "/links", label: t("Useful links") },
    { href: "/preorder", label: t("Pre-order") },
    { href: "/contacts", label: t("Contacts") },
  ];
}
