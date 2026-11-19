/**
 * Thin fetch wrapper for the Django REST API.
 *
 * Server code uses `API_URL` (internal address), browser code uses
 * `NEXT_PUBLIC_API_URL`. Every request carries `Accept-Language`, so the API
 * answers in the active site language.
 */

import type { Locale } from "@/i18n/config";

const DEFAULT_API_URL = "http://127.0.0.1:8000";

export function getApiBaseUrl(): string {
  const url =
    (typeof window === "undefined" ? process.env.API_URL : undefined) ??
    process.env.NEXT_PUBLIC_API_URL ??
    DEFAULT_API_URL;
  return url.replace(/\/+$/, "");
}

export function apiUrl(path: string): string {
  return `${getApiBaseUrl()}${path.startsWith("/") ? path : `/${path}`}`;
}

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly url: string,
    readonly body: unknown,
  ) {
    super(`API request failed with status ${status}: ${url}`);
    this.name = "ApiError";
  }
}

export type ApiFetchOptions = RequestInit & { locale?: Locale };

export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { locale, headers, ...init } = options;
  const url = apiUrl(path);
  const response = await fetch(url, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(locale ? { "Accept-Language": locale } : {}),
      ...headers,
    },
  });

  const isJson = response.headers.get("content-type")?.includes("application/json");
  const body: unknown = isJson ? await response.json() : await response.text();
  if (!response.ok) throw new ApiError(response.status, url, body);
  return body as T;
}
