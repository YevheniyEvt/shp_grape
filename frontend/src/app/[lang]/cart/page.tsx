import type { Metadata } from "next";

import { CartView } from "@/components/cart/cart-view";
import { getTranslator } from "@/i18n/server";

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getTranslator();
  return { title: t("Cart"), robots: { index: false } };
}

/** The shell is static; the cart itself lives in the browser (localStorage). */
export default async function CartPage() {
  const { t } = await getTranslator();
  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <h1 className="mb-8 text-3xl font-semibold sm:text-4xl">{t("Cart")}</h1>
      <CartView />
    </div>
  );
}
