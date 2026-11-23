/** Helpers shared by the site forms: the phone mask and server validation errors. */

const UA_PREFIX = "+380";

/** Digits typed after `+380`, at most nine (operator code + number). */
function localDigits(value: string): string {
  let digits = value.replace(/\D/g, "");
  if (digits.startsWith("380")) digits = digits.slice(3);
  else if (digits.startsWith("80")) digits = digits.slice(2);
  // A national number never starts with 0: `+380 ` + `050…` typed by habit is `+380 50…`.
  return digits.replace(/^0+/, "").slice(0, 9);
}

/**
 * Mask a Ukrainian phone while typing: `+380 (50) 123-45-67`.
 *
 * Accepts any input (`050…`, `+38 050…`, pasted numbers) and always keeps the `+380` prefix.
 */
export function formatPhone(value: string): string {
  const digits = localDigits(value);
  if (!digits) return value.trim() ? `${UA_PREFIX} ` : "";
  const parts = [digits.slice(0, 2), digits.slice(2, 5), digits.slice(5, 7), digits.slice(7, 9)];
  let result = `${UA_PREFIX} (${parts[0]}`;
  if (digits.length > 2) result += `) ${parts[1]}`;
  if (digits.length > 5) result += `-${parts[2]}`;
  if (digits.length > 7) result += `-${parts[3]}`;
  return result;
}

/** A complete Ukrainian number: `+380` and nine more digits. */
export function isCompletePhone(value: string): boolean {
  return /^380\d{9}$/.test(value.replace(/\D/g, ""));
}

/**
 * Field errors from a DRF validation response: `{field: ["message", ...]}` → `{field: "message"}`.
 * Non-field and nested errors are skipped.
 */
export function fieldErrors(body: unknown): Record<string, string> {
  const errors: Record<string, string> = {};
  if (!body || typeof body !== "object" || Array.isArray(body)) return errors;
  for (const [field, value] of Object.entries(body)) {
    if (Array.isArray(value) && typeof value[0] === "string") errors[field] = value[0];
    else if (typeof value === "string" && field !== "detail") errors[field] = value;
  }
  return errors;
}
