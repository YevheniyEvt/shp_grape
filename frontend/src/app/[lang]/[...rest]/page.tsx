import { notFound } from "next/navigation";

// This route only renders the 404 page, so instant-navigation validation is pointless here.
export const instant = false;

/** Any URL that matches no route renders the localized not-found page. */
export default function CatchAllPage() {
  notFound();
}
