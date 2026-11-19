import type { Metadata } from "next";
import { Suspense } from "react";

import { CardGridSkeleton } from "@/components/catalog/catalog-skeleton";
import { PublicationList } from "@/components/content/publications";
import { getTranslator } from "@/i18n/server";

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getTranslator();
  return { title: t("Articles"), description: t("Articles about growing table grapes.") };
}

export default async function ArticlesPage({ searchParams }: PageProps<"/[lang]/articles">) {
  const { t } = await getTranslator();
  return (
    <div className="mx-auto max-w-7xl px-4 py-10">
      <h1 className="mb-8 text-3xl font-semibold sm:text-4xl">{t("Articles")}</h1>
      <Suspense fallback={<CardGridSkeleton count={6} />}>
        <PublicationList kind="articles" searchParams={searchParams} />
      </Suspense>
    </div>
  );
}
