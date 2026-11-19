import { ShoppingBasketIcon, StarIcon } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Locale } from "@/i18n/config";
import type { Translator } from "@/i18n/gettext";
import type { VarietyListItem } from "@/lib/api/catalog";
import { formatNumber, formatPrice, formatRange, lowestPrice } from "@/lib/format";

import { VarietyImage } from "./variety-image";

export function isInStock(
  variety: Pick<VarietyListItem, "cutting_available" | "sapling_available">,
): boolean {
  return Boolean(variety.cutting_available || variety.sapling_available);
}

/** Availability badge shared by the card and the variety page. */
export function StockBadge({ inStock, t }: { inStock: boolean; t: Translator["t"] }) {
  return inStock ? (
    <Badge className="bg-accent text-accent-foreground">{t("In stock")}</Badge>
  ) : (
    <Badge variant="outline" className="text-muted-foreground">
      {t("Out of stock")}
    </Badge>
  );
}

type Fact = { label: string; value: string };

/** Catalog card: photo, name, badges, key characteristics and the lowest price. */
export function VarietyCard({
  variety,
  href,
  locale,
  t,
  preload = false,
}: {
  variety: VarietyListItem;
  href: string;
  locale: Locale;
  t: Translator["t"];
  preload?: boolean;
}) {
  const bunch = formatRange(variety.bunch_weight_min, variety.bunch_weight_max, locale);
  const berry = formatRange(variety.berry_weight_min, variety.berry_weight_max, locale);
  const price = lowestPrice([variety.cutting_price, variety.sapling_price]);
  const facts: Fact[] = [];
  if (bunch) facts.push({ label: t("Bunch"), value: t("%(value)s kg", { value: bunch }) });
  if (berry) facts.push({ label: t("Berry"), value: t("%(value)s g", { value: berry }) });
  if (typeof variety.frost_resistance === "number") {
    facts.push({
      label: t("Frost resistance"),
      value: t("%(value)s °C", { value: formatNumber(variety.frost_resistance, locale) }),
    });
  }

  return (
    <article className="group relative flex flex-col overflow-hidden rounded-xl bg-card ring-1 ring-foreground/10 transition-shadow hover:shadow-lg">
      <div className="relative aspect-4/3 overflow-hidden">
        <VarietyImage
          photo={variety.main_photo}
          className="size-full transition-transform duration-500 group-hover:scale-105"
          sizes="(min-width: 1280px) 25vw, (min-width: 1024px) 33vw, (min-width: 640px) 50vw, 100vw"
          preload={preload}
        />
        {variety.is_featured && (
          <Badge className="absolute top-3 left-3 shadow">
            <StarIcon aria-hidden="true" />
            {t("Recommended")}
          </Badge>
        )}
      </div>

      <div className="flex flex-1 flex-col gap-3 p-4">
        <div className="flex flex-wrap gap-1.5">
          {variety.ripening && <Badge variant="secondary">{variety.ripening.name}</Badge>}
          <StockBadge inStock={isInStock(variety)} t={t} />
        </div>

        <h3 className="font-heading text-lg leading-snug font-semibold">
          {/* The whole card is clickable through the stretched link. */}
          <Link href={href} className="after:absolute after:inset-0 hover:text-primary">
            {variety.name}
          </Link>
        </h3>

        {facts.length > 0 && (
          <dl className="grid gap-1 text-sm">
            {facts.map((fact) => (
              <div key={fact.label} className="flex justify-between gap-2">
                <dt className="text-muted-foreground">{fact.label}</dt>
                <dd className="font-medium">{fact.value}</dd>
              </div>
            ))}
          </dl>
        )}

        <div className="mt-auto flex items-center justify-between gap-2 pt-2">
          <span className="font-semibold text-primary">
            {price !== null && t("from %(price)s", { price: formatPrice(price, locale) })}
          </span>
          {/* Cart arrives in stage 6; the button sits above the stretched link. */}
          <Button
            size="sm"
            variant="outline"
            className="relative z-10"
            disabled
            title={t("Ordering will be available soon")}
          >
            <ShoppingBasketIcon aria-hidden="true" />
            {t("Add to cart")}
          </Button>
        </div>
      </div>
    </article>
  );
}
