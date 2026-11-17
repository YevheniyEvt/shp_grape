import { ArrowRightIcon, GrapeIcon } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { getTranslator, localizedHref } from "@/i18n/server";

export default async function HomePage() {
  const { t } = await getTranslator();

  return (
    <section className="relative overflow-hidden">
      <div className="absolute inset-0 -z-10 bg-linear-to-br from-primary/15 via-background to-accent/40" />
      <div className="mx-auto flex max-w-7xl flex-col items-start gap-6 px-4 py-20 sm:py-28">
        <span className="inline-flex items-center gap-2 rounded-full bg-accent px-3 py-1 text-sm font-medium text-accent-foreground">
          <GrapeIcon className="size-4" aria-hidden="true" />
          {t("Table grape varieties for every garden")}
        </span>
        <h1 className="max-w-3xl text-4xl leading-tight font-semibold sm:text-5xl lg:text-6xl">
          {t("Vineyard")}
        </h1>
        <p className="max-w-2xl text-lg text-muted-foreground">
          {t("Grape cuttings and seedlings of table varieties from our own vineyard.")}
        </p>
        <div className="flex flex-wrap gap-3">
          <Button size="lg" asChild>
            <Link href={await localizedHref("/catalog")}>
              {t("Variety catalog")}
              <ArrowRightIcon aria-hidden="true" />
            </Link>
          </Button>
          <Button size="lg" variant="outline" asChild>
            <Link href={await localizedHref("/preorder")}>{t("Pre-order")}</Link>
          </Button>
        </div>
      </div>
    </section>
  );
}
