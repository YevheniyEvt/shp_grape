"use client";

import { MailIcon, MenuIcon, PhoneIcon } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { phoneHref, type NavItem } from "@/config/site";
import { useT } from "@/i18n/client";
import type { SiteLanguage } from "@/i18n/server";

import { LanguageSwitcher } from "./language-switcher";

/** Burger menu for small screens: navigation, language switcher and contacts. */
export function MobileMenu({
  nav,
  languages,
  phones,
  email,
}: {
  nav: NavItem[];
  languages: SiteLanguage[];
  phones: string[];
  email?: string;
}) {
  const { t, href } = useT();

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="lg:hidden" aria-label={t("Open menu")}>
          <MenuIcon aria-hidden="true" />
        </Button>
      </SheetTrigger>
      <SheetContent side="right" className="w-80 max-w-[85vw]">
        <SheetHeader>
          <SheetTitle>{t("Menu")}</SheetTitle>
        </SheetHeader>
        <nav aria-label={t("Main menu")} className="flex flex-col px-4">
          {nav.map((item) => (
            <SheetClose asChild key={item.href}>
              <Link
                href={href(item.href)}
                className="rounded-md px-2 py-2.5 text-base font-medium hover:bg-muted"
              >
                {item.label}
              </Link>
            </SheetClose>
          ))}
        </nav>
        <Separator className="my-2" />
        <div className="flex flex-col gap-3 px-6 text-sm">
          {phones.map((phone) => (
            <a key={phone} href={phoneHref(phone)} className="flex items-center gap-2">
              <PhoneIcon className="size-4 text-primary" aria-hidden="true" />
              {phone}
            </a>
          ))}
          {email && (
            <a href={`mailto:${email}`} className="flex items-center gap-2">
              <MailIcon className="size-4 text-primary" aria-hidden="true" />
              {email}
            </a>
          )}
          <div className="-ml-3">
            <LanguageSwitcher languages={languages} />
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
