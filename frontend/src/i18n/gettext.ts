/**
 * Minimal gettext runtime over Django's `JSONCatalog` payload.
 *
 * Source strings (msgid) are English. Translations live in Django's
 * `locale/<lang>/LC_MESSAGES/djangojs.po` and reach the frontend via
 * `GET /api/i18n/<lang>/`. Missing translations fall back to the msgid.
 *
 * Keyword names `t`, `nt` and `pt` are what the string extractor looks for.
 */

/** Shape of the response of `django.views.i18n.JSONCatalog`. */
export type DjangoCatalog = {
  catalog: Record<string, string | string[]>;
  plural: string | null;
  formats?: Record<string, unknown>;
};

export type InterpolationValues = Record<string, string | number> | Array<string | number>;

export type Translator = {
  /** gettext: translate a string. */
  t: (msgid: string, values?: InterpolationValues) => string;
  /** ngettext: translate with plural forms chosen by `count`. */
  nt: (singular: string, plural: string, count: number, values?: InterpolationValues) => string;
  /** pgettext: translate a string in a disambiguating context. */
  pt: (context: string, msgid: string, values?: InterpolationValues) => string;
};

/** Gettext context separator used by Django in catalog keys. */
const CONTEXT_SEPARATOR = "\u0004";

/** Default (Germanic) plural rule: index 0 for one, 1 otherwise. */
const germanicPlural = (n: number): number => (n === 1 ? 0 : 1);

// Only digits, `n`, whitespace, parentheses and C-like operators may appear in a
// gettext plural formula. Anything else is rejected before it is evaluated.
const SAFE_PLURAL_FORMULA = /^[\sn0-9()?:%!=<>&|+\-*/]+$/;

/** Compile a gettext plural formula (e.g. `n != 1`) into an index function. */
export function compilePluralFormula(formula: string | null | undefined): (n: number) => number {
  if (!formula || !SAFE_PLURAL_FORMULA.test(formula)) return germanicPlural;
  try {
    const evaluate = new Function("n", `return Number(${formula});`) as (n: number) => number;
    evaluate(1);
    return evaluate;
  } catch {
    return germanicPlural;
  }
}

/**
 * Interpolate Django-style placeholders: `%(name)s` with an object,
 * `%s` with an array (positional), like Django's JS `interpolate()`.
 */
export function interpolate(format: string, values?: InterpolationValues): string {
  if (values === undefined) return format;
  if (Array.isArray(values)) {
    let index = 0;
    return format.replace(/%s/g, () => String(values[index++] ?? ""));
  }
  return format.replace(/%\(([^)]+)\)s/g, (match, name: string) =>
    name in values ? String(values[name]) : match,
  );
}

export function createTranslator(data: DjangoCatalog | null | undefined): Translator {
  const catalog = data?.catalog ?? {};
  const pluralIndex = compilePluralFormula(data?.plural);

  const lookup = (key: string): string | string[] | undefined => catalog[key];

  const t: Translator["t"] = (msgid, values) => {
    const value = lookup(msgid);
    const translated = typeof value === "string" ? value : Array.isArray(value) ? value[0] : msgid;
    return interpolate(translated || msgid, values);
  };

  const pickPlural = (key: string, singular: string, plural: string, count: number): string => {
    const value = lookup(key);
    if (Array.isArray(value)) {
      const form = value[pluralIndex(count)];
      if (form) return form;
    } else if (typeof value === "string" && value) {
      return value;
    }
    return count === 1 ? singular : plural;
  };

  const nt: Translator["nt"] = (singular, plural, count, values) =>
    interpolate(pickPlural(singular, singular, plural, count), values);

  const pt: Translator["pt"] = (context, msgid, values) => {
    const value = lookup(`${context}${CONTEXT_SEPARATOR}${msgid}`);
    const translated = typeof value === "string" && value ? value : msgid;
    return interpolate(translated, values);
  };

  return { t, nt, pt };
}
