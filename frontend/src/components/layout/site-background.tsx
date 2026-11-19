import type { CSSProperties } from "react";

import type { SiteSettings } from "@/lib/api/content";

export const DEFAULT_BACKGROUND = "/images/grape-pattern.svg";

/**
 * Decorative page background fixed behind the content.
 *
 * An uploaded photo covers the viewport under a translucent wash of the theme background,
 * so text stays readable; without a photo the built-in grape pattern is tiled.
 */
export function SiteBackground({
  settings,
}: {
  settings: Pick<SiteSettings, "show_background" | "background_image">;
}) {
  if (!settings.show_background) return null;

  const photo = settings.background_image;
  const style = { "--site-bg": `url("${photo ?? DEFAULT_BACKGROUND}")` } as CSSProperties;

  return (
    <div
      aria-hidden="true"
      data-testid="site-background"
      data-variant={photo ? "photo" : "pattern"}
      className="site-background"
      style={style}
    />
  );
}
