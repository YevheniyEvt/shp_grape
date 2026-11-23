"use client";

/**
 * Global cart state (Zustand) saved in localStorage.
 *
 * `skipHydration`: the server renders an empty cart, and `<CartHydration />` loads the saved
 * cart after the first client render. That keeps server and client HTML identical (no
 * hydration mismatch); components that show cart data wait for `useCartHydrated()`.
 */

import { useSyncExternalStore } from "react";
import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import {
  addItem,
  applyCheck,
  removeItem,
  setQuantity,
  type CartItem,
  type CheckedLine,
  type Problem,
} from "./cart";

type CartState = {
  items: CartItem[];
  add: (item: CartItem) => void;
  setQuantity: (item: Pick<CartItem, "slug" | "kind">, quantity: number) => void;
  remove: (item: Pick<CartItem, "slug" | "kind">) => void;
  clear: () => void;
  /** Merge the server check into the cart and return the problems found. */
  applyCheck: (lines: CheckedLine[]) => Record<string, Problem>;
};

export const CART_STORAGE_KEY = "vineyard-cart";

export const useCart = create<CartState>()(
  persist(
    (set, get) => ({
      items: [],
      add: (item) => set({ items: addItem(get().items, item) }),
      setQuantity: (item, quantity) => set({ items: setQuantity(get().items, item, quantity) }),
      remove: (item) => set({ items: removeItem(get().items, item) }),
      clear: () => set({ items: [] }),
      applyCheck: (lines) => {
        const { items, problems } = applyCheck(get().items, lines);
        set({ items });
        return problems;
      },
    }),
    {
      name: CART_STORAGE_KEY,
      version: 1,
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ items: state.items }),
      skipHydration: true,
    },
  ),
);

const subscribeHydration = (callback: () => void) => useCart.persist.onFinishHydration(callback);

/** True once the saved cart has been loaded from localStorage (always false on the server). */
export function useCartHydrated(): boolean {
  return useSyncExternalStore(
    subscribeHydration,
    () => useCart.persist.hasHydrated(),
    () => false,
  );
}
