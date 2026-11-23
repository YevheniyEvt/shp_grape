"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2Icon, SendIcon } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";

import {
  FormAlert,
  FormField,
  fieldProps,
  Honeypot,
  SuccessMessage,
  useSubmitErrorMessage,
} from "@/components/forms/form-parts";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useT } from "@/i18n/client";
import { sendContactMessage } from "@/lib/api/orders";
import { contactSchema, type ContactValues } from "@/lib/form-schemas";

const EMPTY: ContactValues = { name: "", email: "", subject: "", message: "", website: "" };

/** Feedback form on the contacts page; the message goes to the owner's email. */
export function ContactForm() {
  const { t, locale } = useT();
  const errorMessage = useSubmitErrorMessage();
  const [sent, setSent] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<ContactValues>({ resolver: zodResolver(contactSchema(t)), defaultValues: EMPTY });

  if (sent) {
    return (
      <SuccessMessage
        title={t("Thank you! Your message is sent.")}
        text={t("We will reply to your email soon.")}
      />
    );
  }

  const onSubmit = async (values: ContactValues) => {
    setSubmitError(null);
    const error = await sendContactMessage(values, locale);
    if (!error) {
      setSent(true);
      return;
    }
    if (error.kind === "validation") {
      for (const [field, message] of Object.entries(error.fields)) {
        if (field in EMPTY) setError(field as keyof ContactValues, { message });
      }
    }
    setSubmitError(errorMessage(error));
  };

  return (
    <form noValidate onSubmit={handleSubmit(onSubmit)} className="relative grid gap-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <FormField id="contact-name" label={t("Your name")} required error={errors.name?.message}>
          <Input
            {...fieldProps("contact-name", errors.name?.message)}
            autoComplete="name"
            {...register("name")}
          />
        </FormField>
        <FormField id="contact-email" label={t("Email")} required error={errors.email?.message}>
          <Input
            {...fieldProps("contact-email", errors.email?.message)}
            type="email"
            autoComplete="email"
            {...register("email")}
          />
        </FormField>
      </div>
      <FormField id="contact-subject" label={t("Subject")} error={errors.subject?.message}>
        <Input
          {...fieldProps("contact-subject", errors.subject?.message)}
          {...register("subject")}
        />
      </FormField>
      <FormField id="contact-message" label={t("Message")} required error={errors.message?.message}>
        <Textarea
          {...fieldProps("contact-message", errors.message?.message)}
          rows={5}
          {...register("message")}
        />
      </FormField>
      <Honeypot registration={register("website")} />
      {submitError && <FormAlert>{submitError}</FormAlert>}
      <div>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? (
            <Loader2Icon className="animate-spin" aria-hidden="true" />
          ) : (
            <SendIcon aria-hidden="true" />
          )}
          {isSubmitting ? t("Sending…") : t("Send")}
        </Button>
      </div>
    </form>
  );
}
