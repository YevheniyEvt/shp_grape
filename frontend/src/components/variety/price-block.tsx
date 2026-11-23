"use client";

import { useState } from "react";

import { AddToCartButton, type CartProduct } from "@/components/cart/add-to-cart-button";
import { QuantityInput } from "@/components/cart/quantity-input";
import { useT } from "@/i18n/client";
import type { ProductKind } from "@/lib/cart/cart";
import { formatPrice } from "@/lib/format";
import { cn } from "@/lib/utils";

export type Offer = { kind: ProductKind; price: number | null; available: boolean };

/** Prices and availability; choose cuttings or saplings and a quantity, then add to the cart. */
export function PriceBlock({ product, offers }: { product: CartProduct; offers: Offer[] }) {
  const { t, locale } = useT();
  const labels: Record<ProductKind, string> = { cutting: t("Cutting"), sapling: t("Sapling") };
  const purchasable = offers.filter((offer) => offer.available && offer.price !== null);
  const [kind, setKind] = useState<ProductKind | undefined>(purchasable[0]?.kind);
  const [quantity, setQuantity] = useState(1);
  const selected = purchasable.find((offer) => offer.kind === kind);

  return (
    <div className="grid gap-4 rounded-xl bg-card p-5 ring-1 ring-foreground/10">
      <div role="radiogroup" aria-label={t("Product type")} className="grid gap-2">
        {offers.map((offer) => {
          const enabled = offer.available && offer.price !== null;
          const checked = enabled && offer.kind === kind;
          return (
            <button
              key={offer.kind}
              type="button"
              role="radio"
              aria-checked={checked}
              disabled={!enabled}
              onClick={() => setKind(offer.kind)}
              className={cn(
                "flex items-center justify-between gap-3 rounded-lg border px-4 py-3 text-left transition",
                checked ? "border-primary bg-primary/5" : "hover:border-primary/50",
                !enabled && "cursor-not-allowed opacity-60",
              )}
            >
              <span className="font-medium">{labels[offer.kind]}</span>
              <span className="text-sm">
                {offer.price !== null && (
                  <span className="font-semibold">{formatPrice(offer.price, locale)}</span>
                )}{" "}
                <span
                  className={offer.available ? "text-accent-foreground" : "text-muted-foreground"}
                >
                  {offer.available ? t("in stock") : t("out of stock")}
                </span>
              </span>
            </button>
          );
        })}
      </div>

      {selected && selected.price !== null && (
        <div className="flex flex-wrap items-center gap-3 print:hidden">
          <QuantityInput value={quantity} onChange={setQuantity} />
          <span className="text-lg font-semibold" data-testid="total">
            {formatPrice(selected.price * quantity, locale)}
          </span>
          <AddToCartButton
            className="ml-auto"
            product={product}
            kind={selected.kind}
            price={selected.price}
            quantity={quantity}
          />
        </div>
      )}
      {!purchasable.length && (
        <p className="text-sm text-muted-foreground">{t("This variety is not available now.")}</p>
      )}
    </div>
  );
}
