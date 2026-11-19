import type { Metadata } from "next";
import { Suspense } from "react";

import { CardGridSkeleton } from "@/components/catalog/catalog-skeleton";
import { PublicationList } from "@/components/content/publications";
import { getTranslator } from "@/i18n/server";

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getTranslator();
  return { title: t("News"), description: t("News of our vineyard.") };
}

export default async function NewsPage({ searchParams }: PageProps<"/[lang]/news">) {
  const { t } = await getTranslator();
  return (
    <div className="mx-auto max-w-7xl px-4 py-10">
      <h1 className="mb-8 text-3xl font-semibold sm:text-4xl">{t("News")}</h1>
      <Suspense fallback={<CardGridSkeleton count={6} />}>
        <PublicationList kind="news" searchParams={searchParams} />
      </Suspense>
    </div>
  );
}
