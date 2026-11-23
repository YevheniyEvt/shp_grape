import type { Metadata } from "next";

import { PreorderForm } from "@/components/forms/preorder-form";
import { getTranslator } from "@/i18n/server";

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getTranslator();
  return {
    title: t("Pre-order"),
    description: t("Order cuttings and saplings of varieties that are not available yet."),
  };
}

export default async function PreorderPage() {
  const { t } = await getTranslator();
  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="mb-4 text-3xl font-semibold sm:text-4xl">{t("Pre-order")}</h1>
      <p className="mb-8 text-muted-foreground">
        {t(
          "A variety is sold out or not in the catalog yet? Tell us what you need, and we will reserve it from the next harvest and contact you.",
        )}
      </p>
      <section className="rounded-xl bg-card/95 p-5 shadow-sm ring-1 ring-foreground/10 sm:p-6">
        <PreorderForm />
      </section>
    </div>
  );
}
