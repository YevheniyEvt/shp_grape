import { FileTextIcon, GrapeIcon, MailIcon, PhoneIcon, ShoppingBasketIcon } from "lucide-react";
import Link from "next/link";

import { AlphabetBar } from "@/components/catalog/alphabet-bar";
import { CartCount } from "@/components/cart/cart-count";
import { Button } from "@/components/ui/button";
import { getMainNav, phoneHref, siteName } from "@/config/site";
import { getAlphabet } from "@/i18n/alphabet";
import { localizePath } from "@/i18n/config";
import { getLanguages, getTranslator } from "@/i18n/server";
import { getAvailableLetters } from "@/lib/api/catalog";
import { getSiteSettings } from "@/lib/api/content";

import { LanguageSwitcher } from "./language-switcher";
import { MobileMenu } from "./mobile-menu";

export async function Header() {
  const { t, locale } = await getTranslator();
  const [languages, letters, settings] = await Promise.all([
    getLanguages(),
    getAvailableLetters(locale),
    getSiteSettings(locale),
  ]);
  const nav = getMainNav({ t });
  const href = (path: string) => localizePath(path, locale);

  return (
    <header className="sticky top-0 z-40 border-b bg-background/90 backdrop-blur supports-backdrop-filter:bg-background/75 print:hidden">
      {/* Top bar: contacts and quick links (desktop only) */}
      <div className="hidden border-b bg-secondary/60 text-sm md:block">
        <div className="mx-auto flex max-w-7xl items-center gap-6 px-4 py-1.5">
          {settings.phones.map((phone) => (
            <a
              key={phone}
              href={phoneHref(phone)}
              className="flex items-center gap-1.5 hover:text-primary"
            >
              <PhoneIcon className="size-3.5" aria-hidden="true" />
              {phone}
            </a>
          ))}
          {settings.email && (
            <a
              href={`mailto:${settings.email}`}
              className="flex items-center gap-1.5 hover:text-primary"
            >
              <MailIcon className="size-3.5" aria-hidden="true" />
              {settings.email}
            </a>
          )}
          <div className="ml-auto flex items-center gap-4">
            {settings.price_list && (
              <a
                href={settings.price_list}
                download
                className="flex items-center gap-1.5 hover:text-primary"
              >
                <FileTextIcon className="size-3.5" aria-hidden="true" />
                {t("Price list")}
              </a>
            )}
            <Link href={href("/contacts")} className="font-medium text-primary hover:underline">
              {t("Write to us")}
            </Link>
          </div>
        </div>
      </div>

      {/* Main bar */}
      <div className="mx-auto flex max-w-7xl items-center gap-4 px-4 py-3">
        <Link href={href("/")} className="flex items-center gap-2">
          <span className="flex size-10 items-center justify-center rounded-full bg-primary text-primary-foreground">
            <GrapeIcon aria-hidden="true" />
          </span>
          <span className="font-heading text-lg leading-tight font-semibold">
            {siteName(settings.site_name, { t })}
          </span>
        </Link>

        <nav aria-label={t("Main menu")} className="ml-6 hidden items-center gap-1 lg:flex">
          {nav.map((item) => (
            <Link
              key={item.href}
              href={href(item.href)}
              className="rounded-md px-3 py-2 text-sm font-medium hover:bg-muted hover:text-primary"
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-1">
          <div className="hidden lg:block">
            <LanguageSwitcher languages={languages} />
          </div>
          <Button variant="ghost" size="icon" asChild className="relative">
            <Link href={href("/cart")} aria-label={t("Cart")}>
              <ShoppingBasketIcon aria-hidden="true" />
              <CartCount />
            </Link>
          </Button>
          <MobileMenu
            nav={nav}
            languages={languages}
            phones={settings.phones}
            email={settings.email}
          />
        </div>
      </div>

      {/* Alphabet: quick jump to the catalog by first letter; letters without varieties are muted. */}
      <AlphabetBar
        label={t("Varieties by letter")}
        letters={getAlphabet(locale)}
        available={letters}
        hrefFor={(letter) => `${href("/catalog")}?letter=${encodeURIComponent(letter)}`}
        className="hidden border-t px-4 py-1 md:block"
      />
    </header>
  );
}
