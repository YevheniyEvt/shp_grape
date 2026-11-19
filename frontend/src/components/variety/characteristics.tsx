import type { Locale } from "@/i18n/config";
import type { Translator } from "@/i18n/gettext";
import type { VarietyDetail } from "@/lib/api/catalog";
import { formatNumber, formatRange } from "@/lib/format";

export type Characteristic = { label: string; value: string };

/** Rows of the characteristics table; empty values are left out. */
export function buildCharacteristics(
  variety: VarietyDetail,
  t: Translator["t"],
  locale: Locale,
): Characteristic[] {
  // Each unit is a literal translation call, so the string extractor can find it.
  const range = (
    min: number | null | undefined,
    max: number | null | undefined,
    withUnit: (value: string) => string,
  ) => {
    const value = formatRange(min, max, locale);
    return value && withUnit(value);
  };
  const rows: [string, string | null | undefined][] = [
    [t("Breeder"), variety.author],
    [t("Ripening period"), variety.ripening?.name],
    [t("Berry colour"), variety.berry_color?.name],
    [t("Pulp"), variety.pulp?.name],
    [t("Taste"), variety.taste?.name],
    [t("Growth vigour"), variety.vigor?.name],
    [
      t("Bunch weight"),
      range(variety.bunch_weight_min, variety.bunch_weight_max, (value) =>
        t("%(value)s kg", { value }),
      ),
    ],
    [
      t("Berry weight"),
      range(variety.berry_weight_min, variety.berry_weight_max, (value) =>
        t("%(value)s g", { value }),
      ),
    ],
    [
      t("Berry size"),
      range(variety.berry_size_min, variety.berry_size_max, (value) =>
        t("%(value)s mm", { value }),
      ),
    ],
    [
      t("Disease susceptibility"),
      range(variety.disease_susceptibility_min, variety.disease_susceptibility_max, (value) =>
        t("%(value)s points", { value }),
      ),
    ],
    [
      t("Frost resistance"),
      typeof variety.frost_resistance === "number"
        ? t("down to %(value)s °C", { value: formatNumber(variety.frost_resistance, locale) })
        : null,
    ],
    [t("Also known as"), variety.alt_names],
  ];
  return rows
    .filter((row): row is [string, string] => Boolean(row[1]))
    .map(([label, value]) => ({ label, value }));
}

export function CharacteristicsTable({
  rows,
  caption,
}: {
  rows: Characteristic[];
  caption: string;
}) {
  if (!rows.length) return null;
  return (
    <table className="w-full text-sm">
      <caption className="sr-only">{caption}</caption>
      <tbody>
        {rows.map((row) => (
          <tr key={row.label} className="border-b last:border-0">
            <th scope="row" className="py-2 pr-4 text-left font-normal text-muted-foreground">
              {row.label}
            </th>
            <td className="py-2 text-right font-medium">{row.value}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
