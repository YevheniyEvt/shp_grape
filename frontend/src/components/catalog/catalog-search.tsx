"use client";

import { SearchIcon, XIcon } from "lucide-react";
import { useEffect, useEffectEvent, useState } from "react";

import { Input } from "@/components/ui/input";
import { useDebounce } from "@/hooks/use-debounce";
import { useT } from "@/i18n/client";
import { type CatalogQuery, updateQuery } from "@/lib/catalog-query";

import { useCatalogNavigation } from "./use-catalog-navigation";

export const SEARCH_DELAY = 400;

/** Search by name: the URL is updated once the visitor stops typing. */
export function CatalogSearch({ query, basePath }: { query: CatalogQuery; basePath: string }) {
  const { t } = useT();
  const { navigate } = useCatalogNavigation(basePath);
  const current = query.search ?? "";
  const [value, setValue] = useState(current);
  const [synced, setSynced] = useState(current);

  // The URL changed from outside (reset button, back button): show its value.
  // Adjusting state during render is React's recommended alternative to an effect here.
  if (current !== synced) {
    setSynced(current);
    if (current !== value.trim()) setValue(current);
  }

  const debounced = useDebounce(value, SEARCH_DELAY);

  // An effect event reads the latest query without re-running the effect when it changes.
  const search = useEffectEvent((term: string) => {
    if (term === current) return;
    // Replace, not push: every pause in typing must not become a history entry.
    navigate(updateQuery(query, { search: term || undefined }), { replace: true });
  });

  useEffect(() => {
    search(debounced.trim());
  }, [debounced]);

  return (
    <div className="relative w-full sm:max-w-xs">
      <SearchIcon
        className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground"
        aria-hidden="true"
      />
      <Input
        type="search"
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder={t("Search by name")}
        aria-label={t("Search by name")}
        className="pr-9 pl-9 [&::-webkit-search-cancel-button]:hidden"
      />
      {value && (
        <button
          type="button"
          onClick={() => setValue("")}
          aria-label={t("Clear search")}
          className="absolute top-1/2 right-2 -translate-y-1/2 rounded p-1 text-muted-foreground hover:text-foreground"
        >
          <XIcon className="size-4" aria-hidden="true" />
        </button>
      )}
    </div>
  );
}
