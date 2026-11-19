import { ExternalLinkIcon } from "lucide-react";
import type { Metadata } from "next";

import { getTranslator } from "@/i18n/server";
import { getUsefulLinks } from "@/lib/api/content";

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getTranslator();
  return { title: t("Useful links"), description: t("Useful materials about growing grapes.") };
}

export default async function LinksPage() {
  const { t, locale } = await getTranslator();
  const links = await getUsefulLinks(locale);

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="mb-8 text-3xl font-semibold sm:text-4xl">{t("Useful links")}</h1>
      {links.length ? (
        <ul className="grid gap-3">
          {links.map((link) => (
            <li key={link.id}>
              <a
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                className="group flex items-start gap-3 rounded-xl bg-card p-4 ring-1 ring-foreground/10 transition hover:shadow-md"
              >
                <ExternalLinkIcon
                  className="mt-1 size-4 shrink-0 text-primary"
                  aria-hidden="true"
                />
                <span className="grid gap-1">
                  <span className="font-medium group-hover:text-primary">{link.title}</span>
                  {link.description && (
                    <span className="text-sm text-muted-foreground">{link.description}</span>
                  )}
                  <span className="text-xs break-all text-muted-foreground">{link.url}</span>
                </span>
              </a>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-muted-foreground">{t("Nothing has been published yet.")}</p>
      )}
    </div>
  );
}
