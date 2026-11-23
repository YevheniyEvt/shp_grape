/**
 * Pure cart logic: items, quantities, totals and merging the server check (`cart/validate`).
 * The Zustand store (`store.ts`) only wires these functions to state, so they are easy to test.
 */

export type ProductKind = "cutting" | "sapling";

/** The largest quantity of one item (the API has the same limit). */
export const MAX_QUANTITY = 99;

export type CartItem = {
  slug: string;
  kind: ProductKind;
  quantity: number;
  /** Unit price the customer saw; sent with the order so the server can detect changes. */
  price: number;
  name: string;
  image: string | null;
};

export type Problem = "not_found" | "unavailable" | "price_changed";

/** A cart item as `POST /api/cart/validate/` returns it. */
export type CheckedLine = {
  variety: string;
  kind: string;
  quantity: number;
  name: string | null;
  price: number | null;
  available: boolean;
  problem: Problem | null;
  photo: { thumb: string } | null;
};

export function clampQuantity(value: number): number {
  if (!Number.isFinite(value)) return 1;
  return Math.min(MAX_QUANTITY, Math.max(1, Math.round(value)));
}

export const itemKey = (item: { slug: string; kind: string }) => `${item.slug}:${item.kind}`;

const sameItem = (a: { slug: string; kind: string }, b: { slug: string; kind: string }) =>
  a.slug === b.slug && a.kind === b.kind;

/** Add `item` (with its quantity) to the cart; an existing item gets the quantities summed. */
export function addItem(items: CartItem[], item: CartItem): CartItem[] {
  const existing = items.find((current) => sameItem(current, item));
  if (!existing) return [...items, { ...item, quantity: clampQuantity(item.quantity) }];
  return items.map((current) =>
    current === existing
      ? {
          ...current,
          ...item,
          quantity: clampQuantity(current.quantity + item.quantity),
        }
      : current,
  );
}

export function setQuantity(
  items: CartItem[],
  target: Pick<CartItem, "slug" | "kind">,
  quantity: number,
): CartItem[] {
  return items.map((item) =>
    sameItem(item, target) ? { ...item, quantity: clampQuantity(quantity) } : item,
  );
}

export function removeItem(items: CartItem[], target: Pick<CartItem, "slug" | "kind">) {
  return items.filter((item) => !sameItem(item, target));
}

export function cartCount(items: CartItem[]): number {
  return items.reduce((sum, item) => sum + item.quantity, 0);
}

export function cartTotal(items: CartItem[]): number {
  return items.reduce((sum, item) => sum + item.price * item.quantity, 0);
}

/**
 * Update cart items with the server check: current names, photos and prices.
 *
 * Items the server no longer knows are dropped; unavailable ones are kept, so the customer
 * sees what is missing. Returns the new items and the problems keyed by `itemKey`.
 */
export function applyCheck(
  items: CartItem[],
  lines: CheckedLine[],
): { items: CartItem[]; problems: Record<string, Problem> } {
  const byKey = new Map(lines.map((line) => [`${line.variety}:${line.kind}`, line]));
  const problems: Record<string, Problem> = {};
  const updated: CartItem[] = [];
  for (const item of items) {
    const line = byKey.get(itemKey(item));
    if (!line) {
      updated.push(item);
      continue;
    }
    if (line.problem) problems[itemKey(item)] = line.problem;
    if (line.problem === "not_found") continue;
    updated.push({
      ...item,
      name: line.name ?? item.name,
      price: line.price ?? item.price,
      image: line.photo?.thumb ?? item.image,
    });
  }
  return { items: updated, problems };
}
