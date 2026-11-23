"use client";

import type { ComponentProps } from "react";

import { Input } from "@/components/ui/input";
import { formatPhone } from "@/lib/forms";

type PhoneInputProps = Omit<ComponentProps<typeof Input>, "onChange" | "value"> & {
  value: string;
  onChange: (value: string) => void;
};

/** Phone input with the `+380 (50) 123-45-67` mask (use with react-hook-form's `Controller`). */
export function PhoneInput({ value, onChange, onFocus, ...props }: PhoneInputProps) {
  return (
    <Input
      type="tel"
      inputMode="tel"
      autoComplete="tel"
      placeholder="+380 (50) 123-45-67"
      {...props}
      value={value}
      onChange={(event) => onChange(formatPhone(event.target.value))}
      onFocus={(event) => {
        // Start with the country code, so people type only their local number.
        if (!value) onChange("+380 ");
        onFocus?.(event);
      }}
    />
  );
}
