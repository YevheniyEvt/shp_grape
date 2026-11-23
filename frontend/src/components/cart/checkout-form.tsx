"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2Icon, SendIcon } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";

import {
  FormAlert,
  FormField,
  fieldProps,
  Honeypot,
  useSubmitErrorMessage,
} from "@/components/forms/form-parts";
import { PhoneInput } from "@/components/forms/phone-input";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { useT } from "@/i18n/client";
import { placeOrder } from "@/lib/api/orders";
import { itemKey } from "@/lib/cart/cart";
import { useCart } from "@/lib/cart/store";
import { formatPrice } from "@/lib/format";
import { checkoutSchema, CONTACT_METHODS, type CheckoutValues } from "@/lib/form-schemas";
import { cn } from "@/lib/utils";

import { CartNotices, orderableItems, useCartCheck } from "./cart-view";

const EMPTY: CheckoutValues = {
  full_name: "",
  phone: "",
  email: "",
  city: "",
  delivery_office: "",
  contact_method: "phone",
  comment: "",
  website: "",
};

/** Order summary next to the form: items, quantities and the total. */
function OrderSummary() {
  const { t, locale } = useT();
  const items = useCart((state) => state.items);
  const total = items.reduce((sum, item) => sum + item.price * item.quantity, 0);
  return (
    <aside
      aria-labelledby="order-summary"
      className="grid content-start gap-3 rounded-xl bg-card p-5 ring-1 ring-foreground/10"
    >
      <h2 id="order-summary" className="text-xl font-semibold">
        {t("Your order")}
      </h2>
      <ul className="grid gap-2 text-sm">
        {items.map((item) => (
          <li key={itemKey(item)} className="flex justify-between gap-3">
            <span>
              {item.name}, {item.kind === "cutting" ? t("cutting") : t("sapling")} × {item.quantity}
            </span>
            <span className="tabular-nums">{formatPrice(item.price * item.quantity, locale)}</span>
          </li>
        ))}
      </ul>
      <p className="flex justify-between border-t pt-3 text-lg font-semibold">
        <span>{t("Total")}</span>
        <span className="tabular-nums" data-testid="checkout-total">
          {formatPrice(total, locale)}
        </span>
      </p>
    </aside>
  );
}

export function CheckoutForm() {
  const { t, locale, href } = useT();
  const router = useRouter();
  const items = useCart((state) => state.items);
  const { hydrated, problems, setProblems, removed } = useCartCheck();
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [placed, setPlaced] = useState(false);
  const errorMessage = useSubmitErrorMessage();
  const contactLabels: Record<(typeof CONTACT_METHODS)[number], string> = {
    phone: t("Phone call"),
    viber: "Viber",
    telegram: "Telegram",
    email: t("Email"),
  };

  const {
    register,
    control,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<CheckoutValues>({ resolver: zodResolver(checkoutSchema(t)), defaultValues: EMPTY });

  if (!hydrated) return <Skeleton className="h-96 w-full" />;

  if (placed) {
    return (
      <p role="status" className="flex items-center gap-2 text-lg">
        <Loader2Icon className="animate-spin" aria-hidden="true" />
        {t("The order is placed. Opening the confirmation…")}
      </p>
    );
  }

  if (!items.length) {
    return (
      <div className="grid justify-items-center gap-4 rounded-xl bg-card p-10 text-center ring-1 ring-foreground/10">
        <p className="text-lg">{t("Your cart is empty.")}</p>
        <Button asChild>
          <Link href={href("/catalog")}>{t("Go to the catalog")}</Link>
        </Button>
      </div>
    );
  }

  const blocked = orderableItems(items, problems).length !== items.length;

  const onSubmit = async (values: CheckoutValues) => {
    setSubmitError(null);
    const result = await placeOrder(values, useCart.getState().items, locale);
    if (result.ok) {
      // `placed` replaces the form, so the emptied cart does not flash "Your cart is empty".
      setPlaced(true);
      useCart.getState().clear();
      router.push(href(`/order/success/${encodeURIComponent(result.number)}`));
      return;
    }
    if (result.kind === "conflict") {
      setProblems(useCart.getState().applyCheck(result.items));
      setSubmitError(result.detail);
      return;
    }
    if (result.kind === "validation") {
      for (const [field, message] of Object.entries(result.fields)) {
        if (field in EMPTY) setError(field as keyof CheckoutValues, { message });
      }
    }
    setSubmitError(errorMessage(result));
  };

  return (
    <div className="grid gap-8 lg:grid-cols-[1fr_22rem]">
      <form
        noValidate
        onSubmit={handleSubmit(onSubmit)}
        className="relative grid gap-5 rounded-xl bg-card p-5 ring-1 ring-foreground/10 sm:p-6"
      >
        <CartNotices problems={problems} removed={removed} />
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField
            id="checkout-name"
            label={t("Full name")}
            required
            error={errors.full_name?.message}
          >
            <Input
              {...fieldProps("checkout-name", errors.full_name?.message)}
              autoComplete="name"
              {...register("full_name")}
            />
          </FormField>
          <FormField id="checkout-phone" label={t("Phone")} required error={errors.phone?.message}>
            <Controller
              name="phone"
              control={control}
              render={({ field }) => (
                <PhoneInput
                  {...fieldProps("checkout-phone", errors.phone?.message)}
                  name={field.name}
                  ref={field.ref}
                  value={field.value}
                  onChange={field.onChange}
                  onBlur={field.onBlur}
                />
              )}
            />
          </FormField>
          <FormField
            id="checkout-email"
            label={t("Email")}
            error={errors.email?.message}
            hint={t("We will send the order confirmation there.")}
          >
            <Input
              {...fieldProps("checkout-email", errors.email?.message, "hint")}
              type="email"
              autoComplete="email"
              {...register("email")}
            />
          </FormField>
          <FormField id="checkout-city" label={t("City")} error={errors.city?.message}>
            <Input
              {...fieldProps("checkout-city", errors.city?.message)}
              autoComplete="address-level2"
              {...register("city")}
            />
          </FormField>
        </div>
        <FormField
          id="checkout-office"
          label={t("Nova Poshta office")}
          error={errors.delivery_office?.message}
          hint={t("Branch or parcel locker number.")}
        >
          <Input
            {...fieldProps("checkout-office", errors.delivery_office?.message, "hint")}
            {...register("delivery_office")}
          />
        </FormField>
        <fieldset className="grid gap-2">
          <legend className="mb-1.5 text-sm font-medium">{t("How should we contact you?")}</legend>
          <div className="flex flex-wrap gap-2">
            {CONTACT_METHODS.map((method) => (
              <label
                key={method}
                className={cn(
                  "flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-sm transition",
                  "has-checked:border-primary has-checked:bg-primary/5 has-focus-visible:ring-3 has-focus-visible:ring-ring/50",
                )}
              >
                <input
                  type="radio"
                  value={method}
                  className="accent-primary"
                  {...register("contact_method")}
                />
                {contactLabels[method]}
              </label>
            ))}
          </div>
        </fieldset>
        <FormField id="checkout-comment" label={t("Comment")} error={errors.comment?.message}>
          <Textarea
            {...fieldProps("checkout-comment", errors.comment?.message)}
            rows={3}
            {...register("comment")}
          />
        </FormField>
        <Honeypot registration={register("website")} />

        {submitError && (
          <FormAlert>
            {submitError}{" "}
            {blocked && (
              <Link href={href("/cart")} className="font-medium underline">
                {t("Go to cart")}
              </Link>
            )}
          </FormAlert>
        )}

        <div className="flex flex-wrap items-center gap-3">
          <Button type="submit" size="lg" disabled={isSubmitting || blocked}>
            {isSubmitting ? (
              <Loader2Icon className="animate-spin" aria-hidden="true" />
            ) : (
              <SendIcon aria-hidden="true" />
            )}
            {isSubmitting ? t("Sending…") : t("Place the order")}
          </Button>
          <p className="text-sm text-muted-foreground">
            {t("We will contact you to confirm the order, delivery and payment.")}
          </p>
        </div>
      </form>
      <OrderSummary />
    </div>
  );
}
