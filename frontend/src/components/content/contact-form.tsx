"use client";

import { SendIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useT } from "@/i18n/client";

/** Feedback form. Only the interface for now: sending arrives with orders in stage 6. */
export function ContactForm() {
  const { t } = useT();

  return (
    <form
      className="grid gap-4"
      aria-describedby="contact-form-note"
      onSubmit={(event) => event.preventDefault()}
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="grid gap-1.5">
          <Label htmlFor="contact-name">{t("Your name")}</Label>
          <Input id="contact-name" name="name" autoComplete="name" required />
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="contact-email">{t("Email")}</Label>
          <Input id="contact-email" name="email" type="email" autoComplete="email" required />
        </div>
      </div>
      <div className="grid gap-1.5">
        <Label htmlFor="contact-subject">{t("Subject")}</Label>
        <Input id="contact-subject" name="subject" />
      </div>
      <div className="grid gap-1.5">
        <Label htmlFor="contact-message">{t("Message")}</Label>
        <textarea
          id="contact-message"
          name="message"
          rows={5}
          required
          className="rounded-lg border border-input bg-card px-3 py-2 text-sm shadow-xs outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50"
        />
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <Button type="submit" disabled>
          <SendIcon aria-hidden="true" />
          {t("Send")}
        </Button>
        <p id="contact-form-note" className="text-sm text-muted-foreground">
          {t("Sending messages will be available soon. Please call or email us for now.")}
        </p>
      </div>
    </form>
  );
}
