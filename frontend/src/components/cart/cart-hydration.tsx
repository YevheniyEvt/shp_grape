"use client";

import { useEffect } from "react";

import { CART_STORAGE_KEY, useCart } from "@/lib/cart/store";

/**
 * Load the saved cart after the first render and keep it in sync between browser tabs.
 * Rendered once in the root layout; renders nothing.
 */
export function CartHydration() {
  useEffect(() => {
    void useCart.persist.rehydrate();
    const onStorage = (event: StorageEvent) => {
      if (event.key === CART_STORAGE_KEY) void useCart.persist.rehydrate();
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);
  return null;
}
