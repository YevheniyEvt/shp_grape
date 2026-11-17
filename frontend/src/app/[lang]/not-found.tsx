import Link from "next/link";

import { Button } from "@/components/ui/button";
import { getTranslator, localizedHref } from "@/i18n/server";

export default async function NotFound() {
  const { t } = await getTranslator();

  return (
    <section className="mx-auto flex max-w-7xl flex-col items-start gap-4 px-4 py-24">
      <p className="text-sm font-semibold text-primary">404</p>
      <h1 className="text-3xl font-semibold sm:text-4xl">{t("Page not found")}</h1>
      <p className="text-muted-foreground">
        {t("The page you are looking for does not exist or has been moved.")}
      </p>
      <Button asChild>
        <Link href={await localizedHref("/")}>{t("Go to home page")}</Link>
      </Button>
    </section>
  );
}
