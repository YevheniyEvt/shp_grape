"use client";

import { useEffect } from "react";

import { registerView } from "@/lib/api/views";

export const viewedKey = (slug: string) => `viewed:${slug}`;

/** Count a page view once per browser session (the API also throttles by visitor). */
export function ViewCounter({ slug }: { slug: string }) {
  useEffect(() => {
    try {
      if (sessionStorage.getItem(viewedKey(slug))) return;
      sessionStorage.setItem(viewedKey(slug), "1");
    } catch {
      // Storage may be blocked (private mode); count the view anyway.
    }
    void registerView(slug);
  }, [slug]);

  return null;
}
