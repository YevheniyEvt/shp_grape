import { HammerIcon } from "lucide-react";

import { getTranslator } from "@/i18n/server";

/** Placeholder content for sections implemented in later stages. */
export async function PageStub({ title }: { title: string }) {
  const { t } = await getTranslator();

  return (
    <section className="mx-auto max-w-7xl px-4 py-16">
      <h1 className="text-3xl font-semibold sm:text-4xl">{title}</h1>
      <p className="mt-6 flex items-center gap-2 text-muted-foreground">
        <HammerIcon className="size-4" aria-hidden="true" />
        {t("This section is under construction.")}
      </p>
    </section>
  );
}
