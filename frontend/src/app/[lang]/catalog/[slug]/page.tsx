import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { VarietyDetailsSkeleton } from "@/components/variety/variety-details-skeleton";
import { VarietyDetails } from "@/components/variety/variety-details";
import { getTranslator } from "@/i18n/server";
import { getVariety } from "@/lib/api/catalog";
import { plainText } from "@/lib/format";

export async function generateMetadata({
  params,
}: PageProps<"/[lang]/catalog/[slug]">): Promise<Metadata> {
  const { slug } = await params;
  const { t, locale } = await getTranslator();
  const variety = await getVariety(locale, slug);
  if (!variety) notFound();

  const description =
    plainText(variety.description, 160) ||
    t("Grape variety %(name)s: photos, characteristics and prices.", { name: variety.name });
  const image = variety.main_photo;
  return {
    title: variety.name,
    description,
    openGraph: {
      title: variety.name,
      description,
      ...(image && {
        images: [
          {
            url: image.large,
            width: image.width ?? undefined,
            height: image.height ?? undefined,
            alt: image.alt,
          },
        ],
      }),
    },
  };
}

export default function VarietyPage({ params }: PageProps<"/[lang]/catalog/[slug]">) {
  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      {/* The slug is read inside the boundary, so the page shell can be served instantly. */}
      <Suspense fallback={<VarietyDetailsSkeleton />}>
        <VarietyDetails params={params} />
      </Suspense>
    </div>
  );
}
