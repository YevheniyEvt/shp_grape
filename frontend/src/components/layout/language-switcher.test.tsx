import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { I18nProvider } from "@/i18n/client";

import { LanguageSwitcher } from "./language-switcher";

const languages = [
  { code: "uk" as const, name: "Українська", is_default: true },
  { code: "en" as const, name: "English", is_default: false },
];

describe("LanguageSwitcher", () => {
  it("shows the current locale with a translated accessible label", () => {
    render(
      <I18nProvider
        locale="uk"
        catalog={{ catalog: { "Change language": "Змінити мову" }, plural: null }}
      >
        <LanguageSwitcher languages={languages} />
      </I18nProvider>,
    );

    const trigger = screen.getByRole("button", { name: "Змінити мову" });
    expect(trigger).toHaveTextContent("uk");
  });

  it("requires the I18nProvider", () => {
    expect(() => render(<LanguageSwitcher languages={languages} />)).toThrow(/I18nProvider/);
  });
});
