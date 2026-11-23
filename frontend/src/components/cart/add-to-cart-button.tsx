"use client";

import { ShoppingBasketIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import type { ComponentProps } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { useT } from "@/i18n/client";
import type { ProductKind } from "@/lib/cart/cart";
import { useCart } from "@/lib/cart/store";

export type CartProduct = { slug: string; name: string; image: string | null };

/** Adds a product to the cart and confirms it with a toast that links to the cart. */
export function AddToCartButton({
  product,
  kind,
  price,
  quantity = 1,
  label,
  ...props
}: {
  product: CartProduct;
  kind: ProductKind;
  price: number;
  quantity?: number;
  label?: string;
} & Omit<ComponentProps<typeof Button>, "onClick">) {
  const { t, href } = useT();
  const router = useRouter();
  const add = useCart((state) => state.add);
  const kindLabel = kind === "cutting" ? t("Cutting") : t("Sapling");

  return (
    <Button
      {...props}
      onClick={() => {
        add({ ...product, kind, price, quantity });
        toast.success(t("Added to cart"), {
          description: `${product.name} — ${kindLabel.toLowerCase()} × ${quantity}`,
          action: { label: t("Go to cart"), onClick: () => router.push(href("/cart")) },
        });
      }}
    >
      <ShoppingBasketIcon aria-hidden="true" />
      {label ?? t("Add to cart")}
    </Button>
  );
}
