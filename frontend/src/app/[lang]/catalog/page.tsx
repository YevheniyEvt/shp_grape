import type { Metadata } from "next";

import { PageStub } from "@/components/common/page-stub";
import { getTranslator } from "@/i18n/server";

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getTranslator();
  return { title: t("Variety catalog") };
}

export default async function CatalogPage() {
  const { t } = await getTranslator();
  return <PageStub title={t("Variety catalog")} />;
}
