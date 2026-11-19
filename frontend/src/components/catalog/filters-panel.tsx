"use client";

import { SlidersHorizontalIcon } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Slider } from "@/components/ui/slider";
import { useT } from "@/i18n/client";
import type { FilterOptions } from "@/lib/api/catalog";
import {
  type CatalogQuery,
  countActiveFilters,
  DICTIONARY_FILTERS,
  type DictionaryFilter,
  type NumberRange,
  RANGE_FILTERS,
  type RangeFilter,
  resetFilters,
  setRange,
  toggleDictionaryValue,
  updateQuery,
} from "@/lib/catalog-query";
import { formatNumber } from "@/lib/format";
import { cn } from "@/lib/utils";

import { useCatalogNavigation } from "./use-catalog-navigation";

/** Slider step of every range, in the units the API uses. */
export const RANGE_STEPS: Record<RangeFilter, number> = {
  bunch_weight: 0.1,
  berry_weight: 0.5,
  berry_size: 1,
  disease: 0.5,
  frost: 1,
};

/**
 * Turn slider positions into a filter: a thumb left at the edge of the data means
 * "no bound", so the URL only carries what the visitor actually narrowed.
 */
export function sliderToRange(
  [low, high]: number[],
  bounds: { min: number; max: number },
): NumberRange {
  return {
    ...(low > bounds.min && { min: low }),
    ...(high < bounds.max && { max: high }),
  };
}

type Props = { query: CatalogQuery; options: FilterOptions; basePath: string };

export function FiltersPanel({ query, options, basePath }: Props) {
  const { t, locale } = useT();
  const { navigate, isPending } = useCatalogNavigation(basePath);

  const dictionaryLabels: Record<DictionaryFilter, string> = {
    ripening: t("Ripening period"),
    berry_color: t("Berry colour"),
    pulp: t("Pulp"),
    taste: t("Taste"),
    vigor: t("Growth vigour"),
  };
  const rangeLabels: Record<RangeFilter, string> = {
    bunch_weight: t("Bunch weight, kg"),
    berry_weight: t("Berry weight, g"),
    berry_size: t("Berry size, mm"),
    disease: t("Disease susceptibility, points"),
    frost: t("Frost resistance, °C"),
  };

  return (
    <div
      className={cn("grid gap-6 transition-opacity", isPending && "opacity-60")}
      aria-busy={isPending}
    >
      <label className="flex cursor-pointer items-center gap-2 text-sm font-medium">
        <Checkbox
          checked={query.inStock}
          onCheckedChange={(checked) => navigate(updateQuery(query, { inStock: checked === true }))}
        />
        {t("In stock only")}
      </label>

      {DICTIONARY_FILTERS.map((name) =>
        options[name].length ? (
          <fieldset key={name} className="grid gap-2">
            <legend className="mb-2 text-sm font-semibold">{dictionaryLabels[name]}</legend>
            {options[name].map((item) => (
              <label key={item.slug} className="flex cursor-pointer items-center gap-2 text-sm">
                <Checkbox
                  checked={query.dictionaries[name].includes(item.slug)}
                  onCheckedChange={() => navigate(toggleDictionaryValue(query, name, item.slug))}
                />
                {item.name}
              </label>
            ))}
          </fieldset>
        ) : null,
      )}

      {RANGE_FILTERS.map((name) => {
        const { min, max } = options.ranges[name];
        if (min === null || max === null || min >= max) return null;
        return (
          <RangeField
            key={`${name}:${query.ranges[name].min}:${query.ranges[name].max}`}
            label={rangeLabels[name]}
            bounds={{ min, max }}
            step={RANGE_STEPS[name]}
            value={query.ranges[name]}
            format={(value) => formatNumber(value, locale)}
            onCommit={(range) => navigate(setRange(query, name, range))}
          />
        );
      })}

      <Button
        variant="outline"
        disabled={countActiveFilters(query) === 0}
        onClick={() => navigate(resetFilters(query))}
      >
        {t("Reset filters")}
      </Button>
    </div>
  );
}

function RangeField({
  label,
  bounds,
  step,
  value,
  format,
  onCommit,
}: {
  label: string;
  bounds: { min: number; max: number };
  step: number;
  value: NumberRange;
  format: (value: number) => string;
  onCommit: (range: NumberRange) => void;
}) {
  // Local state while dragging; the URL changes only when the thumb is released.
  const [current, setCurrent] = useState([value.min ?? bounds.min, value.max ?? bounds.max]);

  return (
    <div className="grid gap-3">
      <div className="flex items-baseline justify-between gap-2 text-sm">
        <span className="font-semibold">{label}</span>
        <span className="text-muted-foreground tabular-nums">
          {format(current[0])} – {format(current[1])}
        </span>
      </div>
      <Slider
        min={bounds.min}
        max={bounds.max}
        step={step}
        value={current}
        minStepsBetweenThumbs={0}
        onValueChange={setCurrent}
        onValueCommit={(next) => onCommit(sliderToRange(next, bounds))}
        aria-label={label}
      />
    </div>
  );
}

/** Mobile: the same panel in a side sheet, opened by a button with the active filter count. */
export function MobileFilters(props: Props) {
  const { t } = useT();
  const count = countActiveFilters(props.query);

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" className="lg:hidden">
          <SlidersHorizontalIcon aria-hidden="true" />
          {t("Filters")}
          {count > 0 && <Badge className="ml-1">{count}</Badge>}
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-80 overflow-y-auto">
        <SheetHeader>
          <SheetTitle>{t("Filters")}</SheetTitle>
          <SheetDescription className="sr-only">
            {t("Narrow down the variety list")}
          </SheetDescription>
        </SheetHeader>
        <div className="px-4 pb-6">
          <FiltersPanel {...props} />
        </div>
      </SheetContent>
    </Sheet>
  );
}
