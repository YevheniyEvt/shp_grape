import { CircleCheckIcon } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { localizePath } from "@/i18n/config";
import { getTranslator } from "@/i18n/server";

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getTranslator();
  return { title: t("Thank you for your order"), robots: { index: false } };
}

/** The order number comes from the URL only: the page shows no order data. */
async function OrderNumber({ params }: { params: Promise<{ number: string }> }) {
  const { number } = await params;
  const { t } = await getTranslator();
  return (
    <p className="text-lg">
      {t("Your order number is")}{" "}
      <strong className="font-semibold tabular-nums" data-testid="order-number">
        {number}
      </strong>
    </p>
  );
}

export default async function OrderSuccessPage({
  params,
}: PageProps<"/[lang]/order/success/[number]">) {
  const { t, locale } = await getTranslator();
  return (
    <div className="mx-auto max-w-2xl px-4 py-16">
      <div className="grid justify-items-center gap-4 rounded-xl bg-card p-8 text-center shadow-sm ring-1 ring-foreground/10">
        <CircleCheckIcon className="size-14 text-accent-foreground" aria-hidden="true" />
        <h1 className="text-3xl font-semibold">{t("Thank you for your order!")}</h1>
        <Suspense fallback={<Skeleton className="h-7 w-64" />}>
          <OrderNumber params={params} />
        </Suspense>
        <p className="text-muted-foreground">
          {t(
            "We will contact you soon to confirm the order and arrange the delivery. If you left an email, the confirmation is already there.",
          )}
        </p>
        <Button asChild>
          <Link href={localizePath("/catalog", locale)}>{t("Back to the catalog")}</Link>
        </Button>
      </div>
    </div>
  );
}
