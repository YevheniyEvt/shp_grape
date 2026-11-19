import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { DEFAULT_BACKGROUND, SiteBackground } from "./site-background";

describe("SiteBackground", () => {
  afterEach(cleanup);

  it("tiles the built-in grape pattern when no photo is uploaded", () => {
    render(<SiteBackground settings={{ show_background: true, background_image: null }} />);

    const layer = screen.getByTestId("site-background");
    expect(layer).toHaveAttribute("data-variant", "pattern");
    expect(layer).toHaveAttribute("aria-hidden", "true");
    expect(layer.style.getPropertyValue("--site-bg")).toBe(`url("${DEFAULT_BACKGROUND}")`);
  });

  it("covers the page with the uploaded photo", () => {
    const photo = "http://127.0.0.1:8000/media/cache/bg.webp";
    render(<SiteBackground settings={{ show_background: true, background_image: photo }} />);

    const layer = screen.getByTestId("site-background");
    expect(layer).toHaveAttribute("data-variant", "photo");
    expect(layer.style.getPropertyValue("--site-bg")).toBe(`url("${photo}")`);
  });

  it("renders nothing when the background is switched off", () => {
    const { container } = render(
      <SiteBackground settings={{ show_background: false, background_image: null }} />,
    );
    expect(container).toBeEmptyDOMElement();
  });
});
