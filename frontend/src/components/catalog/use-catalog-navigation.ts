"use client";

import { useRouter } from "next/navigation";
import { useCallback, useTransition } from "react";

import { type CatalogQuery, catalogHref } from "@/lib/catalog-query";

/**
 * Move the catalog to another query by changing the URL.
 *
 * The URL is the single source of truth: the server page re-renders with the new
 * `searchParams`, and the browser's back button restores previous filters.
 * `isPending` is true while the new list is loading.
 */
export function useCatalogNavigation(basePath: string) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  const navigate = useCallback(
    (query: CatalogQuery, { replace = false }: { replace?: boolean } = {}) => {
      const href = catalogHref(basePath, query);
      startTransition(() => {
        if (replace) router.replace(href, { scroll: false });
        else router.push(href, { scroll: false });
      });
    },
    [basePath, router],
  );

  return { navigate, isPending };
}
