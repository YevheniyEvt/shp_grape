"use client";

import { MinusIcon, PlusIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useT } from "@/i18n/client";
import { clampQuantity, MAX_QUANTITY } from "@/lib/cart/cart";

/** `− [n] +` quantity control, limited to 1…MAX_QUANTITY. */
export function QuantityInput({
  value,
  onChange,
  label,
}: {
  value: number;
  onChange: (value: number) => void;
  label?: string;
}) {
  const { t } = useT();
  return (
    <div className="flex items-center rounded-lg border bg-card">
      <Button
        variant="ghost"
        size="icon"
        aria-label={t("Decrease quantity")}
        onClick={() => onChange(clampQuantity(value - 1))}
        disabled={value <= 1}
      >
        <MinusIcon aria-hidden="true" />
      </Button>
      <input
        type="number"
        inputMode="numeric"
        min={1}
        max={MAX_QUANTITY}
        value={value}
        onChange={(event) => onChange(clampQuantity(Number(event.target.value)))}
        aria-label={label ?? t("Quantity")}
        className="w-12 [appearance:textfield] bg-transparent text-center font-medium tabular-nums outline-none [&::-webkit-inner-spin-button]:appearance-none"
      />
      <Button
        variant="ghost"
        size="icon"
        aria-label={t("Increase quantity")}
        onClick={() => onChange(clampQuantity(value + 1))}
        disabled={value >= MAX_QUANTITY}
      >
        <PlusIcon aria-hidden="true" />
      </Button>
    </div>
  );
}
