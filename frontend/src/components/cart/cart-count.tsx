"use client";

import { Badge } from "@/components/ui/badge";
import { cartCount } from "@/lib/cart/cart";
import { useCart, useCartHydrated } from "@/lib/cart/store";

/** Number of items on the header cart icon; hidden until the saved cart is loaded or when empty. */
export function CartCount() {
  const hydrated = useCartHydrated();
  const count = useCart((state) => cartCount(state.items));
  if (!hydrated || count === 0) return null;
  return (
    <Badge
      className="absolute -top-1 -right-1 h-5 min-w-5 px-1 text-[10px] tabular-nums"
      data-testid="cart-count"
    >
      {count > 99 ? "99+" : count}
    </Badge>
  );
}
