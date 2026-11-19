import type { Metadata } from "next";
import { Lora, Manrope } from "next/font/google";

import { Footer } from "@/components/layout/footer";
import { Header } from "@/components/layout/header";
import { SiteBackground } from "@/components/layout/site-background";
import { I18nProvider } from "@/i18n/client";
import { locales } from "@/i18n/config";
import { getCatalog, getLocale, getTranslator } from "@/i18n/server";
import { siteName } from "@/config/site";
import { getSiteSettings } from "@/lib/api/content";

import "../globals.css";

const manrope = Manrope({
  variable: "--font-manrope",
  subsets: ["latin", "cyrillic"],
});

const lora = Lora({
  variable: "--font-lora",
  subsets: ["latin", "cyrillic"],
});

export async function generateStaticParams() {
  return locales.map((lang) => ({ lang }));
}

export async function generateMetadata(): Promise<Metadata> {
  const { t, locale } = await getTranslator();
  const name = siteName((await getSiteSettings(locale)).site_name, { t });
  return {
    title: { default: name, template: `%s · ${name}` },
    description: t("Grape cuttings and seedlings of table varieties from our own vineyard."),
  };
}

export default async function RootLayout({ children }: LayoutProps<"/[lang]">) {
  const locale = await getLocale();
  const [catalog, siteSettings] = await Promise.all([getCatalog(locale), getSiteSettings(locale)]);

  return (
    <html lang={locale} className={`${manrope.variable} ${lora.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">
        <SiteBackground settings={siteSettings} />
        <I18nProvider locale={locale} catalog={catalog}>
          <Header />
          <main className="flex-1">{children}</main>
          <Footer />
        </I18nProvider>
      </body>
    </html>
  );
}
