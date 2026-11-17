import type { Locale } from "./config";

/** Letters shown in the catalog alphabet bar for each locale. */
const ALPHABETS: Record<Locale, string> = {
  uk: "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЮЯ",
  en: "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
};

export function getAlphabet(locale: Locale): string[] {
  return Array.from(ALPHABETS[locale]);
}
