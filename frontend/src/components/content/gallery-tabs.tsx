import Link from "next/link";

import type { Translator } from "@/i18n/gettext";
import { cn } from "@/lib/utils";

/** "Albums | All photos" switch of the gallery section. */
export function GalleryTabs({
  active,
  hrefFor,
  t,
}: {
  active: "albums" | "all";
  hrefFor: (path: string) => string;
  t: Translator["t"];
}) {
  const tabs = [
    { key: "albums", href: hrefFor("/gallery"), label: t("Albums") },
    { key: "all", href: hrefFor("/gallery/all"), label: t("All photos") },
  ] as const;
  return (
    <nav aria-label={t("Gallery")} className="mb-8 flex gap-1 rounded-lg bg-muted p-1 sm:w-fit">
      {tabs.map((tab) => (
        <Link
          key={tab.key}
          href={tab.href}
          aria-current={tab.key === active ? "page" : undefined}
          className={cn(
            "flex-1 rounded-md px-4 py-1.5 text-center text-sm font-medium transition sm:flex-none",
            tab.key === active
              ? "bg-background shadow-sm"
              : "text-muted-foreground hover:text-foreground",
          )}
        >
          {tab.label}
        </Link>
      ))}
    </nav>
  );
}
