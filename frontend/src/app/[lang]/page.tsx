import {
  ArrowRightIcon,
  GrapeIcon,
  PackageCheckIcon,
  PhoneCallIcon,
  SearchIcon,
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";

import { VarietyCard } from "@/components/catalog/variety-card";
import { RichText } from "@/components/common/rich-text";
import { PublicationCard } from "@/components/content/publication-card";
import { Button } from "@/components/ui/button";
import { siteName } from "@/config/site";
import { localizePath } from "@/i18n/config";
import { getTranslator } from "@/i18n/server";
import { getHome, getSiteSettings } from "@/lib/api/content";

function SectionHeader({
  title,
  href,
  linkLabel,
}: {
  title: string;
  href: string;
  linkLabel: string;
}) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-2">
      <h2 className="text-2xl font-semibold sm:text-3xl">{title}</h2>
      <Link
        href={href}
        className="flex items-center gap-1 text-sm font-medium text-primary hover:underline"
      >
        {linkLabel}
        <ArrowRightIcon className="size-4" aria-hidden="true" />
      </Link>
    </div>
  );
}

export default async function HomePage() {
  const { t, locale } = await getTranslator();
  const [home, settings] = await Promise.all([getHome(locale), getSiteSettings(locale)]);
  const href = (path: string) => localizePath(path, locale);
  const name = siteName(settings.site_name, { t });

  const steps = [
    {
      icon: SearchIcon,
      title: t("Choose varieties"),
      text: t("Use the catalog filters to find varieties for your region and taste."),
    },
    {
      icon: PhoneCallIcon,
      title: t("Place an order"),
      text: t("Send a pre-order or call us: we will confirm availability and the price."),
    },
    {
      icon: PackageCheckIcon,
      title: t("Receive the parcel"),
      text: t("We pack cuttings and saplings carefully and ship them in the planting season."),
    },
  ];

  return (
    <>
      {/* Hero: the photo from the admin, or the theme gradient. */}
      <section className="relative isolate overflow-hidden">
        {home.hero_image ? (
          <>
            <Image
              src={home.hero_image}
              alt=""
              fill
              preload
              unoptimized
              sizes="100vw"
              className="-z-20 object-cover"
            />
            <div className="absolute inset-0 -z-10 bg-linear-to-r from-background via-background/85 to-background/30" />
          </>
        ) : (
          <div className="absolute inset-0 -z-10 bg-linear-to-br from-primary/15 via-background to-accent/40" />
        )}
        <div className="mx-auto flex max-w-7xl flex-col items-start gap-6 px-4 py-20 sm:py-28">
          <span className="inline-flex items-center gap-2 rounded-full bg-accent px-3 py-1 text-sm font-medium text-accent-foreground">
            <GrapeIcon className="size-4" aria-hidden="true" />
            {t("Table grape varieties for every garden")}
          </span>
          <h1 className="max-w-3xl text-4xl leading-tight font-semibold sm:text-5xl lg:text-6xl">
            {name}
          </h1>
          <p className="max-w-2xl text-lg text-muted-foreground">
            {settings.tagline ||
              t("Grape cuttings and seedlings of table varieties from our own vineyard.")}
          </p>
          <div className="flex flex-wrap gap-3">
            <Button size="lg" asChild>
              <Link href={href("/catalog")}>
                {t("Variety catalog")}
                <ArrowRightIcon aria-hidden="true" />
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link href={href("/preorder")}>{t("Pre-order")}</Link>
            </Button>
          </div>
        </div>
      </section>

      <div className="mx-auto grid max-w-7xl gap-16 px-4 py-16">
        {(home.welcome || home.latest_news) && (
          <section className="grid gap-10 lg:grid-cols-3" aria-labelledby="about-vineyard">
            <div className={home.latest_news ? "lg:col-span-2" : "lg:col-span-3"}>
              <h2 id="about-vineyard" className="mb-4 text-2xl font-semibold sm:text-3xl">
                {t("About the vineyard")}
              </h2>
              <RichText html={home.welcome} />
              <Link
                href={href("/about")}
                className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
              >
                {t("More about us")}
                <ArrowRightIcon className="size-4" aria-hidden="true" />
              </Link>
            </div>
            {home.latest_news && (
              <aside aria-labelledby="latest-news">
                <h2 id="latest-news" className="mb-4 text-xl font-semibold">
                  {t("Latest news")}
                </h2>
                <PublicationCard
                  item={home.latest_news}
                  href={href(`/news/${home.latest_news.slug}`)}
                  locale={locale}
                />
              </aside>
            )}
          </section>
        )}

        {home.featured_varieties.length > 0 && (
          <section aria-label={t("Recommended varieties")}>
            <SectionHeader
              title={t("Recommended varieties")}
              href={href("/catalog")}
              linkLabel={t("Whole catalog")}
            />
            <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {home.featured_varieties.map((variety) => (
                <li key={variety.id} className="flex">
                  <VarietyCard
                    variety={variety}
                    href={href(`/catalog/${variety.slug}`)}
                    locale={locale}
                    t={t}
                  />
                </li>
              ))}
            </ul>
          </section>
        )}

        <section aria-labelledby="how-to-order" className="rounded-2xl bg-secondary/60 p-8">
          <h2 id="how-to-order" className="mb-8 text-2xl font-semibold sm:text-3xl">
            {t("How to order")}
          </h2>
          <ol className="grid gap-8 md:grid-cols-3">
            {steps.map((step, index) => (
              <li key={step.title} className="flex gap-4">
                <span className="flex size-12 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                  <step.icon aria-hidden="true" />
                </span>
                <div>
                  <h3 className="font-semibold">
                    {index + 1}. {step.title}
                  </h3>
                  <p className="mt-1 text-sm text-muted-foreground">{step.text}</p>
                </div>
              </li>
            ))}
          </ol>
        </section>

        {home.latest_articles.length > 0 && (
          <section aria-label={t("Latest articles")}>
            <SectionHeader
              title={t("Latest articles")}
              href={href("/articles")}
              linkLabel={t("All articles")}
            />
            <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {home.latest_articles.map((article) => (
                <li key={article.id}>
                  <PublicationCard
                    item={article}
                    href={href(`/articles/${article.slug}`)}
                    locale={locale}
                  />
                </li>
              ))}
            </ul>
          </section>
        )}

        <section className="flex flex-col items-start gap-4 rounded-2xl bg-primary p-8 text-primary-foreground sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-2xl font-semibold">{t("Did not find the variety you need?")}</h2>
            <p className="mt-1 text-primary-foreground/80">
              {t("Leave a pre-order and we will let you know when it is available.")}
            </p>
          </div>
          <Button size="lg" variant="secondary" asChild>
            <Link href={href("/preorder")}>{t("Pre-order")}</Link>
          </Button>
        </section>
      </div>
    </>
  );
}
