import { NextResponse, type NextRequest } from "next/server";

import { LOCALE_COOKIE } from "@/i18n/config";
import { resolveLocaleRoute } from "@/i18n/routing";

export function proxy(request: NextRequest) {
  const action = resolveLocaleRoute(
    request.nextUrl.pathname,
    request.cookies.get(LOCALE_COOKIE)?.value,
  );

  if (action.type === "next") return NextResponse.next();

  const url = request.nextUrl.clone();
  url.pathname = action.pathname;
  return action.type === "redirect" ? NextResponse.redirect(url) : NextResponse.rewrite(url);
}

export const config = {
  // Skip Next.js internals, API routes and files with an extension (images, favicon, ...).
  matcher: ["/((?!api|_next/static|_next/image|.*\\..*).*)"],
};
