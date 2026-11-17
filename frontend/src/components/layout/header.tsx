import { FileTextIcon, GrapeIcon, MailIcon, PhoneIcon, ShoppingBasketIcon } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getMainNav, phoneHref, siteContacts } from "@/config/site";
import { getAlphabet } from "@/i18n/alphabet";
import { localizePath } from "@/i18n/config";
import { getLanguages, getTranslator } from "@/i18n/server";

import { LanguageSwitcher } from "./language-switcher";
import { MobileMenu } from "./mobile-menu";

export async function Header() {
  const { t, locale } = await getTranslator();
  const languages = await getLanguages();
  const nav = getMainNav({ t });
  const href = (path: string) => localizePath(path, locale);

  return (
    <header className="sticky top-0 z-40 border-b bg-background/90 backdrop-blur supports-backdrop-filter:bg-background/75">
      {/* Top bar: contacts and quick links (desktop only) */}
      <div className="hidden border-b bg-secondary/60 text-sm md:block">
        <div className="mx-auto flex max-w-7xl items-center gap-6 px-4 py-1.5">
          {siteContacts.phones.map((phone) => (
            <a
              key={phone}
              href={phoneHref(phone)}
              className="flex items-center gap-1.5 hover:text-primary"
            >
              <PhoneIcon className="size-3.5" aria-hidden="true" />
              {phone}
            </a>
          ))}
          <a
            href={`mailto:${siteContacts.email}`}
            className="flex items-center gap-1.5 hover:text-primary"
          >
            <MailIcon className="size-3.5" aria-hidden="true" />
            {siteContacts.email}
          </a>
          <div className="ml-auto flex items-center gap-4">
            {/* Points to the price list file from SiteSettings in stage 5. */}
            <Link href={href("/catalog")} className="flex items-center gap-1.5 hover:text-primary">
              <FileTextIcon className="size-3.5" aria-hidden="true" />
              {t("Price list")}
            </Link>
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
          <span className="font-heading text-lg leading-tight font-semibold">{t("Vineyard")}</span>
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
              <Badge className="absolute -top-1 -right-1 h-5 min-w-5 px-1 text-[10px]">0</Badge>
            </Link>
          </Button>
          <MobileMenu nav={nav} languages={languages} />
        </div>
      </div>

      {/* Alphabet: quick jump to catalog by first letter (stub until stage 4) */}
      <nav aria-label={t("Varieties by letter")} className="hidden border-t md:block">
        <div className="mx-auto flex max-w-7xl flex-wrap justify-center gap-x-1 px-4 py-1">
          {getAlphabet(locale).map((letter) => (
            <Link
              key={letter}
              href={`${href("/catalog")}?letter=${encodeURIComponent(letter)}`}
              className="rounded px-1.5 py-0.5 text-xs font-medium text-muted-foreground hover:bg-muted hover:text-primary"
            >
              {letter}
            </Link>
          ))}
        </div>
      </nav>
    </header>
  );
}
