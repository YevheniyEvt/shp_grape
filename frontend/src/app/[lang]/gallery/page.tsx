import type { Metadata } from "next";

import { PageStub } from "@/components/common/page-stub";
import { getTranslator } from "@/i18n/server";

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getTranslator();
  return { title: t("Gallery") };
}

export default async function GalleryPage() {
  const { t } = await getTranslator();
  return <PageStub title={t("Gallery")} />;
}
