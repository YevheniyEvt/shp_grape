"use client";

import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useT } from "@/i18n/client";
import { type CatalogQuery, type Ordering, ORDERINGS, updateQuery } from "@/lib/catalog-query";

import { useCatalogNavigation } from "./use-catalog-navigation";

const DEFAULT_ORDERING: Ordering = "name";

export function SortSelect({ query, basePath }: { query: CatalogQuery; basePath: string }) {
  const { t } = useT();
  const { navigate } = useCatalogNavigation(basePath);
  const labels: Record<Ordering, string> = {
    name: t("By name"),
    ripening: t("By ripening period"),
    "-created": t("Newest first"),
    "-views_count": t("Most popular"),
  };

  return (
    <div className="flex items-center gap-2">
      <Label htmlFor="catalog-sort" className="text-sm whitespace-nowrap text-muted-foreground">
        {t("Sort")}
      </Label>
      <Select
        value={query.ordering ?? DEFAULT_ORDERING}
        onValueChange={(value) =>
          navigate(
            updateQuery(query, {
              ordering: value === DEFAULT_ORDERING ? undefined : (value as Ordering),
            }),
          )
        }
      >
        <SelectTrigger id="catalog-sort" className="w-48">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {ORDERINGS.map((ordering) => (
            <SelectItem key={ordering} value={ordering}>
              {labels[ordering]}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
