"use client";

import { MinusIcon, PlusIcon, ShoppingBasketIcon } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { useT } from "@/i18n/client";
import { formatPrice } from "@/lib/format";
import { cn } from "@/lib/utils";

export type ProductKind = "cutting" | "sapling";
export type Offer = { kind: ProductKind; price: number | null; available: boolean };

export const MAX_QUANTITY = 99;

export function clampQuantity(value: number): number {
  if (!Number.isFinite(value)) return 1;
  return Math.min(MAX_QUANTITY, Math.max(1, Math.round(value)));
}

/** Prices and availability; choose cuttings or saplings and a quantity (the cart is stage 6). */
export function PriceBlock({ offers }: { offers: Offer[] }) {
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

      {selected && (
        <div className="flex flex-wrap items-center gap-3 print:hidden">
          <div className="flex items-center rounded-lg border">
            <Button
              variant="ghost"
              size="icon"
              aria-label={t("Decrease quantity")}
              onClick={() => setQuantity((value) => clampQuantity(value - 1))}
              disabled={quantity <= 1}
            >
              <MinusIcon aria-hidden="true" />
            </Button>
            <input
              type="number"
              inputMode="numeric"
              min={1}
              max={MAX_QUANTITY}
              value={quantity}
              onChange={(event) => setQuantity(clampQuantity(Number(event.target.value)))}
              aria-label={t("Quantity")}
              className="w-12 [appearance:textfield] bg-transparent text-center font-medium tabular-nums outline-none [&::-webkit-inner-spin-button]:appearance-none"
            />
            <Button
              variant="ghost"
              size="icon"
              aria-label={t("Increase quantity")}
              onClick={() => setQuantity((value) => clampQuantity(value + 1))}
              disabled={quantity >= MAX_QUANTITY}
            >
              <PlusIcon aria-hidden="true" />
            </Button>
          </div>
          <span className="text-lg font-semibold" data-testid="total">
            {formatPrice((selected.price ?? 0) * quantity, locale)}
          </span>
          <Button className="ml-auto" disabled title={t("Ordering will be available soon")}>
            <ShoppingBasketIcon aria-hidden="true" />
            {t("Add to cart")}
          </Button>
        </div>
      )}
      {!purchasable.length && (
        <p className="text-sm text-muted-foreground">{t("This variety is not available now.")}</p>
      )}
    </div>
  );
}
