import type { Metadata } from "next";
import { Suspense } from "react";

import { CatalogResults } from "@/components/catalog/catalog-results";
import { CatalogSkeleton } from "@/components/catalog/catalog-skeleton";
import { getTranslator } from "@/i18n/server";

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getTranslator();
  return {
    title: t("Variety catalog"),
    description: t("Table grape varieties with photos, characteristics and prices."),
  };
}

export default async function CatalogPage({ searchParams }: PageProps<"/[lang]/catalog">) {
  const { t } = await getTranslator();

  return (
    <div className="mx-auto max-w-7xl px-4 py-10">
      <h1 className="mb-6 text-3xl font-semibold sm:text-4xl">{t("Variety catalog")}</h1>
      {/* The title is prerendered; the list depends on the URL and streams in. */}
      <Suspense fallback={<CatalogSkeleton />}>
        <CatalogResults searchParams={searchParams} />
      </Suspense>
    </div>
  );
}
