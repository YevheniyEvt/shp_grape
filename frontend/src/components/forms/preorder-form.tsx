"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2Icon, SendIcon } from "lucide-react";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useT } from "@/i18n/client";
import { sendPreorder } from "@/lib/api/orders";
import { preorderSchema, type PreorderValues } from "@/lib/form-schemas";

import {
  FormAlert,
  FormField,
  fieldProps,
  Honeypot,
  SuccessMessage,
  useSubmitErrorMessage,
} from "./form-parts";
import { PhoneInput } from "./phone-input";

const EMPTY: PreorderValues = { full_name: "", phone: "", email: "", description: "", website: "" };

/** Pre-order form: what the customer wants for the next season and how to reach them. */
export function PreorderForm() {
  const { t, locale } = useT();
  const errorMessage = useSubmitErrorMessage();
  const [sent, setSent] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const {
    register,
    control,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<PreorderValues>({ resolver: zodResolver(preorderSchema(t)), defaultValues: EMPTY });

  if (sent) {
    return (
      <SuccessMessage
        title={t("Thank you! Your pre-order is sent.")}
        text={t("We will contact you when the varieties are available.")}
      />
    );
  }

  const onSubmit = async (values: PreorderValues) => {
    setSubmitError(null);
    const error = await sendPreorder(values, locale);
    if (!error) {
      setSent(true);
      return;
    }
    if (error.kind === "validation") {
      for (const [field, message] of Object.entries(error.fields)) {
        if (field in EMPTY) setError(field as keyof PreorderValues, { message });
      }
    }
    setSubmitError(errorMessage(error));
  };

  return (
    <form noValidate onSubmit={handleSubmit(onSubmit)} className="relative grid gap-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <FormField
          id="preorder-name"
          label={t("Full name")}
          required
          error={errors.full_name?.message}
        >
          <Input
            {...fieldProps("preorder-name", errors.full_name?.message)}
            autoComplete="name"
            {...register("full_name")}
          />
        </FormField>
        <FormField id="preorder-phone" label={t("Phone")} required error={errors.phone?.message}>
          <Controller
            name="phone"
            control={control}
            render={({ field }) => (
              <PhoneInput
                {...fieldProps("preorder-phone", errors.phone?.message)}
                name={field.name}
                ref={field.ref}
                value={field.value}
                onChange={field.onChange}
                onBlur={field.onBlur}
              />
            )}
          />
        </FormField>
      </div>
      <FormField id="preorder-email" label={t("Email")} error={errors.email?.message}>
        <Input
          {...fieldProps("preorder-email", errors.email?.message)}
          type="email"
          autoComplete="email"
          {...register("email")}
        />
      </FormField>
      <FormField
        id="preorder-description"
        label={t("What would you like to order?")}
        required
        error={errors.description?.message}
        hint={t("Varieties, cuttings or saplings, quantities.")}
      >
        <Textarea
          {...fieldProps("preorder-description", errors.description?.message, "hint")}
          rows={5}
          {...register("description")}
        />
      </FormField>
      <Honeypot registration={register("website")} />
      {submitError && <FormAlert>{submitError}</FormAlert>}
      <div>
        <Button type="submit" size="lg" disabled={isSubmitting}>
          {isSubmitting ? (
            <Loader2Icon className="animate-spin" aria-hidden="true" />
          ) : (
            <SendIcon aria-hidden="true" />
          )}
          {isSubmitting ? t("Sending…") : t("Send the pre-order")}
        </Button>
      </div>
    </form>
  );
}
