import { ChevronRightIcon, EyeIcon, StarIcon } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";

import { isInStock, StockBadge, VarietyCard } from "@/components/catalog/variety-card";
import { Badge } from "@/components/ui/badge";
import { localizePath } from "@/i18n/config";
import { getTranslator } from "@/i18n/server";
import { getVariety } from "@/lib/api/catalog";

import { buildCharacteristics, CharacteristicsTable } from "./characteristics";
import { PriceBlock } from "./price-block";
import { PrintButton } from "./print-button";
import { VarietyGallery } from "./variety-gallery";
import { VarietyVideos } from "./variety-videos";
import { ViewCounter } from "./view-counter";

/** Everything on the variety page that depends on the slug. */
export async function VarietyDetails({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const { t, nt, locale } = await getTranslator();
  const variety = await getVariety(locale, slug);
  if (!variety) notFound();

  const href = (path: string) => localizePath(path, locale);
  const characteristics = buildCharacteristics(variety, t, locale);

  return (
    <article className="grid gap-10">
      <ViewCounter slug={variety.slug ?? slug} />

      <nav aria-label={t("Breadcrumbs")} className="print:hidden">
        <ol className="flex flex-wrap items-center gap-1 text-sm text-muted-foreground">
          <li>
            <Link href={href("/")} className="hover:text-primary">
              {t("Home")}
            </Link>
          </li>
          <ChevronRightIcon className="size-4" aria-hidden="true" />
          <li>
            <Link href={href("/catalog")} className="hover:text-primary">
              {t("Catalog")}
            </Link>
          </li>
          <ChevronRightIcon className="size-4" aria-hidden="true" />
          <li aria-current="page" className="text-foreground">
            {variety.name}
          </li>
        </ol>
      </nav>

      <div className="grid gap-8 lg:grid-cols-2">
        <VarietyGallery photos={variety.photos} name={variety.name} />

        <div className="grid content-start gap-6">
          <header className="grid gap-3">
            <div className="flex flex-wrap items-center gap-2">
              {variety.is_featured && (
                <Badge>
                  <StarIcon aria-hidden="true" />
                  {t("Recommended")}
                </Badge>
              )}
              {variety.ripening && <Badge variant="secondary">{variety.ripening.name}</Badge>}
              <StockBadge inStock={isInStock(variety)} t={t} />
            </div>
            <h1 className="text-3xl font-semibold sm:text-4xl">{variety.name}</h1>
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <span className="flex items-center gap-1.5">
                <EyeIcon className="size-4" aria-hidden="true" />
                {nt("%(count)s view", "%(count)s views", variety.views_count, {
                  count: variety.views_count,
                })}
              </span>
              <span className="ml-auto">
                <PrintButton />
              </span>
            </div>
          </header>

          <PriceBlock
            offers={[
              {
                kind: "cutting",
                price: variety.cutting_price ?? null,
                available: Boolean(variety.cutting_available),
              },
              {
                kind: "sapling",
                price: variety.sapling_price ?? null,
                available: Boolean(variety.sapling_available),
              },
            ]}
          />

          <section aria-labelledby="characteristics">
            <h2 id="characteristics" className="mb-2 text-xl font-semibold">
              {t("Characteristics")}
            </h2>
            <CharacteristicsTable rows={characteristics} caption={t("Characteristics")} />
          </section>
        </div>
      </div>

      {variety.description && (
        <section aria-labelledby="description" className="max-w-3xl">
          <h2 id="description" className="mb-3 text-2xl font-semibold">
            {t("Description")}
          </h2>
          {/* The HTML is sanitized by the backend (nh3) with the editor's allow-list. */}
          <div className="rich-text" dangerouslySetInnerHTML={{ __html: variety.description }} />
        </section>
      )}

      {variety.videos.length > 0 && (
        <section aria-labelledby="videos" className="print:hidden">
          <h2 id="videos" className="mb-3 text-2xl font-semibold">
            {t("Videos")}
          </h2>
          <VarietyVideos videos={variety.videos} fallbackTitle={variety.name} />
        </section>
      )}

      {variety.similar.length > 0 && (
        <section aria-labelledby="similar" className="print:hidden">
          <h2 id="similar" className="mb-4 text-2xl font-semibold">
            {t("Similar varieties")}
          </h2>
          <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {variety.similar.map((item) => (
              <li key={item.id} className="flex">
                <VarietyCard
                  variety={item}
                  href={href(`/catalog/${item.slug}`)}
                  locale={locale}
                  t={t}
                />
              </li>
            ))}
          </ul>
        </section>
      )}
    </article>
  );
}
