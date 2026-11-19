import { ExternalLinkIcon, GrapeIcon, MailIcon, MapPinIcon, PhoneIcon } from "lucide-react";
import { cacheLife } from "next/cache";
import Link from "next/link";

import { getMainNav, phoneHref, siteName, socialLinks } from "@/config/site";
import { localizePath } from "@/i18n/config";
import { getTranslator } from "@/i18n/server";
import { getSiteSettings } from "@/lib/api/content";

import { loadRandomPhotos, RandomPhotos } from "./random-photos";

/** Current year, cached so the footer stays part of the static shell. */
async function getCurrentYear(): Promise<number> {
  "use cache";
  cacheLife("days");
  return new Date().getFullYear();
}

export async function Footer() {
  const { t, locale } = await getTranslator();
  const nav = [...getMainNav({ t }), { href: "/about", label: t("About us") }];
  const href = (path: string) => localizePath(path, locale);
  const [year, photos, settings] = await Promise.all([
    getCurrentYear(),
    loadRandomPhotos(locale),
    getSiteSettings(locale),
  ]);
  const name = siteName(settings.site_name, { t });
  const links = socialLinks(settings.social, { t });

  return (
    <footer className="mt-16 border-t bg-secondary text-secondary-foreground print:hidden">
      <div className="mx-auto grid max-w-7xl gap-10 px-4 py-12 sm:grid-cols-2 lg:grid-cols-4">
        <div className="lg:col-span-2">
          <div className="flex items-center gap-2">
            <GrapeIcon className="text-primary" aria-hidden="true" />
            <span className="font-heading text-lg font-semibold">{name}</span>
          </div>
          <p className="mt-3 max-w-md text-sm text-muted-foreground">
            {settings.tagline ||
              t("Grape cuttings and seedlings of table varieties from our own vineyard.")}
          </p>
          <RandomPhotos photos={photos} locale={locale} title={t("From our vineyard")} />
        </div>

        <nav aria-label={t("Site map")}>
          <h2 className="mb-3 text-sm font-semibold">{t("Site map")}</h2>
          <ul className="grid gap-1.5 text-sm">
            {nav.map((item) => (
              <li key={item.href}>
                <Link href={href(item.href)} className="text-muted-foreground hover:text-primary">
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        <div>
          <h2 className="mb-3 text-sm font-semibold">{t("Contacts")}</h2>
          <ul className="grid gap-2 text-sm">
            {settings.phones.map((phone) => (
              <li key={phone}>
                <a href={phoneHref(phone)} className="flex items-center gap-2 hover:text-primary">
                  <PhoneIcon className="size-4" aria-hidden="true" />
                  {phone}
                </a>
              </li>
            ))}
            {settings.email && (
              <li>
                <a
                  href={`mailto:${settings.email}`}
                  className="flex items-center gap-2 hover:text-primary"
                >
                  <MailIcon className="size-4" aria-hidden="true" />
                  {settings.email}
                </a>
              </li>
            )}
            {settings.address && (
              <li className="flex items-start gap-2">
                <MapPinIcon className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
                {settings.address}
              </li>
            )}
          </ul>
          {links.length > 0 && (
            <ul className="mt-4 flex flex-wrap gap-x-4 gap-y-1 text-sm">
              {links.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-muted-foreground hover:text-primary"
                  >
                    {link.label}
                    <ExternalLinkIcon className="size-3" aria-hidden="true" />
                  </a>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
      <div className="border-t py-4 text-center text-xs text-muted-foreground">
        © {year} {name}. {t("All rights reserved.")}
      </div>
    </footer>
  );
}
