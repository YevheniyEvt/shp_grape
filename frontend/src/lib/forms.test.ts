import { describe, expect, it } from "vitest";

import { createTranslator } from "@/i18n/gettext";

import { checkoutSchema, contactSchema, preorderSchema } from "./form-schemas";
import { fieldErrors, formatPhone, isCompletePhone } from "./forms";

const { t } = createTranslator(null);

describe("formatPhone", () => {
  it.each([
    ["", ""],
    ["+", "+380 "],
    ["0", "+380 "],
    ["+380 ", "+380 "],
    ["5", "+380 (5"],
    ["050", "+380 (50"],
    ["0501", "+380 (50) 1"],
    ["050123", "+380 (50) 123"],
    ["0501234", "+380 (50) 123-4"],
    ["050123456", "+380 (50) 123-45-6"],
    ["0501234567", "+380 (50) 123-45-67"],
    ["+38 (050) 123-45-67", "+380 (50) 123-45-67"],
    ["380501234567", "+380 (50) 123-45-67"],
    ["+380 050", "+380 (50"],
    ["80501234567", "+380 (50) 123-45-67"],
    ["+380 (50) 123-45-678", "+380 (50) 123-45-67"],
  ])("%s → %s", (input, expected) => {
    expect(formatPhone(input)).toBe(expected);
  });

  it("checks a complete number", () => {
    expect(isCompletePhone("+380 (50) 123-45-67")).toBe(true);
    expect(isCompletePhone("+380 (50) 123-45-6")).toBe(false);
    expect(isCompletePhone("")).toBe(false);
  });
});

describe("fieldErrors", () => {
  it("takes the first message of every field", () => {
    expect(
      fieldErrors({
        phone: ["Bad phone.", "Second"],
        website: "Spam detected.",
        detail: "Not a field",
        items: [{ quantity: ["Too many"] }],
      }),
    ).toEqual({ phone: "Bad phone.", website: "Spam detected." });
  });

  it("ignores bodies that are not objects", () => {
    expect(fieldErrors(null)).toEqual({});
    expect(fieldErrors("Server error")).toEqual({});
    expect(fieldErrors(["error"])).toEqual({});
  });
});

describe("form schemas", () => {
  const checkout = {
    full_name: " Іван ",
    phone: "+380 (50) 123-45-67",
    email: "",
    city: "",
    delivery_office: "",
    contact_method: "viber",
    comment: "",
    website: "",
  };

  it("accepts a valid checkout and trims text", () => {
    const result = checkoutSchema(t).safeParse(checkout);
    expect(result.success).toBe(true);
    expect(result.data?.full_name).toBe("Іван");
  });

  it("reports translated messages per field", () => {
    const result = checkoutSchema(t).safeParse({
      ...checkout,
      full_name: "  ",
      phone: "+380 (50",
      email: "nope",
      comment: "x".repeat(2001),
    });
    const issues = Object.fromEntries(
      result.error!.issues.map((issue) => [issue.path[0], issue.message]),
    );
    expect(issues).toEqual({
      full_name: "This field is required.",
      phone: "Enter the full phone number.",
      email: "Enter a valid email address.",
      comment: "Too long.",
    });
  });

  it("validates the pre-order and contact forms", () => {
    expect(
      preorderSchema(t).safeParse({
        full_name: "Оля",
        phone: "+380 (67) 123-45-67",
        email: "olia@example.com",
        description: "Рубін",
        website: "",
      }).success,
    ).toBe(true);
    expect(
      contactSchema(t)
        .safeParse({
          name: "Петро",
          email: "",
          subject: "",
          message: "",
          website: "",
        })
        .error?.issues.map((issue) => issue.path[0]),
    ).toEqual(["email", "message"]);
  });
});
