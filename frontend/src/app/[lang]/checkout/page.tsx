import type { Metadata } from "next";

import { CheckoutForm } from "@/components/cart/checkout-form";
import { getTranslator } from "@/i18n/server";

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getTranslator();
  return { title: t("Checkout"), robots: { index: false } };
}

export default async function CheckoutPage() {
  const { t } = await getTranslator();
  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      <h1 className="mb-8 text-3xl font-semibold sm:text-4xl">{t("Checkout")}</h1>
      <CheckoutForm />
    </div>
  );
}
