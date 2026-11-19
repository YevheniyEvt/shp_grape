import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { RichText } from "@/components/common/rich-text";
import { getTranslator } from "@/i18n/server";
import { getContentPage } from "@/lib/api/content";
import { plainText } from "@/lib/format";

/** Slug of the "About us" page created by the `content/0004_default_content` migration. */
const ABOUT_SLUG = "about";

export async function generateMetadata(): Promise<Metadata> {
  const { t, locale } = await getTranslator();
  const page = await getContentPage(locale, ABOUT_SLUG);
  return {
    title: page?.title || t("About us"),
    description: plainText(page?.body, 160) || undefined,
  };
}

export default async function AboutPage() {
  const { locale } = await getTranslator();
  const page = await getContentPage(locale, ABOUT_SLUG);
  if (!page) notFound();

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="mb-8 text-3xl font-semibold sm:text-4xl">{page.title}</h1>
      <RichText html={page.body ?? ""} />
    </div>
  );
}
