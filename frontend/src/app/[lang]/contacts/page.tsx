import { MailIcon, MapPinIcon, PhoneIcon, UserIcon } from "lucide-react";
import type { Metadata } from "next";

import { ContactForm } from "@/components/content/contact-form";
import { mapEmbedUrl, phoneHref } from "@/config/site";
import { getTranslator } from "@/i18n/server";
import { getSiteSettings } from "@/lib/api/content";

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getTranslator();
  return { title: t("Contacts"), description: t("How to contact us and find the vineyard.") };
}

export default async function ContactsPage() {
  const { t, locale } = await getTranslator();
  const settings = await getSiteSettings(locale);

  const cards = [
    settings.owner_name && {
      icon: UserIcon,
      label: t("Owner"),
      content: <span>{settings.owner_name}</span>,
    },
    settings.phones.length > 0 && {
      icon: PhoneIcon,
      label: t("Phones"),
      content: (
        <span className="grid gap-1">
          {settings.phones.map((phone) => (
            <a key={phone} href={phoneHref(phone)} className="hover:text-primary">
              {phone}
            </a>
          ))}
        </span>
      ),
    },
    settings.email && {
      icon: MailIcon,
      label: t("Email"),
      content: (
        <a href={`mailto:${settings.email}`} className="break-all hover:text-primary">
          {settings.email}
        </a>
      ),
    },
    settings.address && {
      icon: MapPinIcon,
      label: t("Address"),
      content: <span>{settings.address}</span>,
    },
  ].filter((card) => Boolean(card)) as {
    icon: typeof UserIcon;
    label: string;
    content: React.ReactNode;
  }[];

  return (
    <div className="mx-auto max-w-7xl px-4 py-10">
      <h1 className="mb-8 text-3xl font-semibold sm:text-4xl">{t("Contacts")}</h1>

      {cards.length > 0 && (
        <ul className="mb-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {cards.map(({ icon: Icon, label, content }) => (
            <li
              key={label}
              className="flex gap-3 rounded-xl bg-card p-5 shadow-sm ring-1 ring-foreground/10"
            >
              <Icon className="mt-0.5 size-5 shrink-0 text-primary" aria-hidden="true" />
              <div className="grid gap-1 text-sm">
                <span className="font-semibold">{label}</span>
                {content}
              </div>
            </li>
          ))}
        </ul>
      )}

      <div className="grid gap-10 lg:grid-cols-2">
        <section
          aria-labelledby="contact-form"
          className="rounded-xl bg-card/95 p-5 shadow-sm ring-1 ring-foreground/10"
        >
          <h2 id="contact-form" className="mb-4 text-2xl font-semibold">
            {t("Write to us")}
          </h2>
          <ContactForm />
        </section>
        {settings.map && (
          <section
            aria-labelledby="map"
            className="rounded-xl bg-card/95 p-5 shadow-sm ring-1 ring-foreground/10"
          >
            <h2 id="map" className="mb-4 text-2xl font-semibold">
              {t("How to find us")}
            </h2>
            {/* `loading="lazy"`: the map loads only when it scrolls into view. */}
            <iframe
              src={mapEmbedUrl(settings.map, locale)}
              title={t("Map")}
              loading="lazy"
              referrerPolicy="no-referrer-when-downgrade"
              className="aspect-4/3 w-full rounded-xl border-0 ring-1 ring-foreground/10"
            />
          </section>
        )}
      </div>
    </div>
  );
}
