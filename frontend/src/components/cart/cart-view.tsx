"use client";

import { ArrowRightIcon, GrapeIcon, InfoIcon, Trash2Icon, XIcon } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useT } from "@/i18n/client";
import { checkCart } from "@/lib/api/orders";
import { itemKey, type CartItem, type Problem } from "@/lib/cart/cart";
import { useCart, useCartHydrated } from "@/lib/cart/store";
import { formatPrice } from "@/lib/format";

import { QuantityInput } from "./quantity-input";

/** Items that can be ordered (no problem, or only a price change the cart already applied). */
export function orderableItems(items: CartItem[], problems: Record<string, Problem>) {
  return items.filter((item) => {
    const problem = problems[itemKey(item)];
    return problem !== "unavailable" && problem !== "not_found";
  });
}

/**
 * Check the cart against the server once it is loaded from localStorage: current prices,
 * names, photos and availability. Returns the problems by item key and the notices to show.
 */
export function useCartCheck() {
  const { locale } = useT();
  const hydrated = useCartHydrated();
  const [problems, setProblems] = useState<Record<string, Problem>>({});
  const [removed, setRemoved] = useState(0);
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (!hydrated) return;
    let cancelled = false;
    const items = useCart.getState().items;
    void checkCart(items, locale).then((result) => {
      if (cancelled) return;
      setChecked(true);
      if (!result) return; // The check failed: keep the cart as it is, the order is checked again.
      const found = useCart.getState().applyCheck(result.items);
      setProblems(found);
      setRemoved(Object.values(found).filter((problem) => problem === "not_found").length);
    });
    return () => {
      cancelled = true;
    };
  }, [hydrated, locale]);

  return { hydrated, checked, problems, setProblems, removed };
}

export function CartNotices({
  problems,
  removed,
}: {
  problems: Record<string, Problem>;
  removed: number;
}) {
  const { t, nt } = useT();
  const values = Object.values(problems);
  const notices: string[] = [];
  if (removed) {
    notices.push(
      nt(
        "%(count)s item is no longer sold and was removed from the cart.",
        "%(count)s items are no longer sold and were removed from the cart.",
        removed,
        { count: removed },
      ),
    );
  }
  if (values.includes("price_changed")) {
    notices.push(t("Prices of some items have changed. The cart shows the current prices."));
  }
  if (values.includes("unavailable")) {
    notices.push(t("Some items are out of stock now. Remove them to place the order."));
  }
  if (!notices.length) return null;
  return (
    <div
      role="status"
      className="flex gap-2 rounded-lg border border-primary/30 bg-card p-3 text-sm"
      data-testid="cart-notices"
    >
      <InfoIcon className="mt-0.5 size-4 shrink-0 text-primary" aria-hidden="true" />
      <ul className="grid gap-1">
        {notices.map((notice) => (
          <li key={notice}>{notice}</li>
        ))}
      </ul>
    </div>
  );
}

function CartRow({ item, problem }: { item: CartItem; problem?: Problem }) {
  const { t, locale, href } = useT();
  const setQuantity = useCart((state) => state.setQuantity);
  const remove = useCart((state) => state.remove);
  const unavailable = problem === "unavailable";
  const kind = item.kind === "cutting" ? t("Cutting") : t("Sapling");

  return (
    <li className="flex flex-wrap items-center gap-4 py-4 sm:flex-nowrap">
      <div className="size-20 shrink-0 overflow-hidden rounded-lg bg-muted">
        {item.image ? (
          // A small thumbnail already rendered as WebP by the backend.
          // eslint-disable-next-line @next/next/no-img-element
          <img src={item.image} alt="" className="size-full object-cover" loading="lazy" />
        ) : (
          <GrapeIcon className="m-auto size-full p-5 text-muted-foreground" aria-hidden="true" />
        )}
      </div>
      <div className="grid min-w-0 flex-1 gap-1">
        <Link
          href={href(`/catalog/${item.slug}`)}
          className="truncate font-semibold hover:text-primary"
        >
          {item.name}
        </Link>
        <span className="text-sm text-muted-foreground">
          {kind} · {formatPrice(item.price, locale)}
        </span>
        {unavailable && (
          <span className="text-sm font-medium text-destructive">{t("Out of stock")}</span>
        )}
      </div>
      <div className="flex w-full items-center gap-3 sm:w-auto">
        {!unavailable && (
          <QuantityInput
            value={item.quantity}
            onChange={(quantity) => setQuantity(item, quantity)}
            label={t("Quantity of %(name)s", { name: item.name })}
          />
        )}
        <span className="ml-auto w-24 text-right font-semibold tabular-nums sm:ml-0">
          {unavailable ? "—" : formatPrice(item.price * item.quantity, locale)}
        </span>
        <Button
          variant="ghost"
          size="icon"
          aria-label={t("Remove %(name)s", { name: item.name })}
          onClick={() => remove(item)}
        >
          <XIcon aria-hidden="true" />
        </Button>
      </div>
    </li>
  );
}

export function CartView() {
  const { t, locale, href } = useT();
  const items = useCart((state) => state.items);
  const clear = useCart((state) => state.clear);
  const { hydrated, problems, removed } = useCartCheck();

  if (!hydrated) {
    return (
      <div className="grid gap-3" aria-busy="true">
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-24 w-full" />
      </div>
    );
  }

  if (!items.length) {
    return (
      <div className="grid justify-items-center gap-4 rounded-xl bg-card p-10 text-center ring-1 ring-foreground/10">
        <CartNotices problems={{}} removed={removed} />
        <p className="text-lg">{t("Your cart is empty.")}</p>
        <Button asChild>
          <Link href={href("/catalog")}>{t("Go to the catalog")}</Link>
        </Button>
      </div>
    );
  }

  const orderable = orderableItems(items, problems);
  const total = orderable.reduce((sum, item) => sum + item.price * item.quantity, 0);
  const blocked = orderable.length !== items.length;

  return (
    <div className="grid gap-6">
      <CartNotices problems={problems} removed={removed} />
      <ul className="divide-y rounded-xl bg-card px-4 ring-1 ring-foreground/10 sm:px-6">
        {items.map((item) => (
          <CartRow key={itemKey(item)} item={item} problem={problems[itemKey(item)]} />
        ))}
      </ul>
      <div className="flex flex-wrap items-center gap-4 rounded-xl bg-card p-4 ring-1 ring-foreground/10 sm:px-6">
        <Button variant="ghost" onClick={clear}>
          <Trash2Icon aria-hidden="true" />
          {t("Clear the cart")}
        </Button>
        <p className="ml-auto text-lg">
          {t("Total")}:{" "}
          <span className="font-semibold tabular-nums" data-testid="cart-total">
            {formatPrice(total, locale)}
          </span>
        </p>
        {blocked ? (
          <Button size="lg" disabled>
            {t("Checkout")}
          </Button>
        ) : (
          <Button size="lg" asChild>
            <Link href={href("/checkout")}>
              {t("Checkout")}
              <ArrowRightIcon aria-hidden="true" />
            </Link>
          </Button>
        )}
      </div>
    </div>
  );
}
