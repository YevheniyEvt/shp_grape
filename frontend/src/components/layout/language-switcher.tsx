"use client";

import { CheckIcon, GlobeIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { rememberLocale, useT } from "@/i18n/client";
import { isLocale, switchLocaleHref } from "@/i18n/config";
import type { SiteLanguage } from "@/i18n/server";

/** Globe icon with a dropdown of site languages; keeps the visitor on the same page. */
export function LanguageSwitcher({ languages }: { languages: SiteLanguage[] }) {
  const { t, locale } = useT();

  function switchTo(code: string) {
    if (!isLocale(code) || code === locale) return;
    rememberLocale(code);
    // A full navigation reloads the root layout with the other language catalog.
    window.location.assign(switchLocaleHref(window.location.href, code));
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm" aria-label={t("Change language")} className="gap-1.5">
          <GlobeIcon aria-hidden="true" />
          <span className="uppercase">{locale}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {languages.map((language) => (
          <DropdownMenuItem
            key={language.code}
            lang={language.code}
            onSelect={() => switchTo(language.code)}
            aria-current={language.code === locale ? "true" : undefined}
          >
            <span className="flex-1">{language.name}</span>
            {language.code === locale && <CheckIcon aria-hidden="true" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
