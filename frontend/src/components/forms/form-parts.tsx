"use client";

import { AlertCircleIcon, CircleCheckIcon } from "lucide-react";
import type { ReactNode } from "react";
import type { UseFormRegisterReturn } from "react-hook-form";

import { Label } from "@/components/ui/label";
import { useT } from "@/i18n/client";
import type { SubmitError } from "@/lib/api/orders";

/** A labelled form field with its error message linked through `aria-describedby`. */
export function FormField({
  id,
  label,
  error,
  required = false,
  hint,
  children,
}: {
  id: string;
  label: string;
  error?: string;
  required?: boolean;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <div className="grid content-start gap-1.5">
      <Label htmlFor={id}>
        {label}
        {required && (
          <span className="text-destructive" aria-hidden="true">
            *
          </span>
        )}
      </Label>
      {children}
      {hint && !error && (
        <p id={`${id}-hint`} className="text-xs text-muted-foreground">
          {hint}
        </p>
      )}
      {error && (
        <p id={`${id}-error`} role="alert" className="text-sm text-destructive">
          {error}
        </p>
      )}
    </div>
  );
}

/** Accessibility attributes of an input inside `FormField`. */
export function fieldProps(id: string, error?: string, hint?: string) {
  return {
    id,
    "aria-invalid": error ? true : undefined,
    "aria-describedby": error ? `${id}-error` : hint ? `${id}-hint` : undefined,
  };
}

/**
 * Anti-spam trap: a field people never see (off-screen, skipped by Tab and screen readers),
 * but bots fill in. The API rejects a request where it has a value.
 */
export function Honeypot({ registration }: { registration: UseFormRegisterReturn }) {
  return (
    <div aria-hidden="true" className="absolute -left-[9999px] h-px w-px overflow-hidden">
      <label>
        Website
        <input type="text" tabIndex={-1} autoComplete="off" {...registration} />
      </label>
    </div>
  );
}

/** Message for a failed submit (validation errors are shown next to the fields instead). */
export function useSubmitErrorMessage() {
  const { t } = useT();
  return (error: SubmitError): string => {
    switch (error.kind) {
      case "throttled":
        return t("Too many requests. Please try again in an hour or call us.");
      case "network":
        return t("No connection to the server. Check the internet and try again.");
      case "validation":
        return t("Please correct the highlighted fields.");
      default:
        return t("Something went wrong on our side. Please try again later or call us.");
    }
  };
}

export function FormAlert({ children }: { children: ReactNode }) {
  return (
    <div
      role="alert"
      className="flex gap-2 rounded-lg border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive"
    >
      <AlertCircleIcon className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
      <div>{children}</div>
    </div>
  );
}

/** Shown instead of a form after it was sent. */
export function SuccessMessage({ title, text }: { title: string; text: string }) {
  return (
    <div role="status" className="grid justify-items-center gap-2 py-6 text-center">
      <CircleCheckIcon className="size-10 text-accent-foreground" aria-hidden="true" />
      <p className="text-xl font-semibold">{title}</p>
      <p className="text-muted-foreground">{text}</p>
    </div>
  );
}
