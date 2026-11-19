/** Navigation and small helpers shared by the layout. Contacts come from `SiteSettings`. */

import type { Translator } from "@/i18n/gettext";
import type { components } from "@/types/api";

type SocialLinks = components["schemas"]["SocialLinks"];

/** Site name from the admin, or the translated default when it is empty. */
export function siteName(name: string | undefined, { t }: Pick<Translator, "t">): string {
  return name?.trim() || t("Vineyard");
}

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

/** Google Maps embed URL for a point; works without an API key. */
export function mapEmbedUrl(map: { latitude: number; longitude: number }, locale: string): string {
  const query = encodeURIComponent(`${map.latitude},${map.longitude}`);
  return `https://maps.google.com/maps?q=${query}&z=13&hl=${locale}&output=embed`;
}

/** Social and community links that are filled in the admin. */
export function socialLinks(
  social: SocialLinks,
  { t }: Pick<Translator, "t">,
): { href: string; label: string }[] {
  const labels: Record<keyof SocialLinks, string> = {
    facebook: "Facebook",
    instagram: "Instagram",
    youtube: "YouTube",
    telegram: "Telegram",
    forum: t("Forum"),
  };
  return (Object.keys(labels) as (keyof SocialLinks)[])
    .filter((key) => social[key])
    .map((key) => ({ href: social[key], label: labels[key] }));
}
