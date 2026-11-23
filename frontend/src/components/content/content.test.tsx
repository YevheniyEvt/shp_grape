import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { t } from "@/components/catalog/test-utils";
import { RichText } from "@/components/common/rich-text";
import { fitSize, toAlbumPhoto } from "@/components/media/photo-album";
import { socialLinks } from "@/config/site";

import { GalleryTabs } from "./gallery-tabs";
import { feedImage } from "./photo-feed";
import { PublicationCard } from "./publication-card";

const image = {
  id: 7,
  alt: "Гроно",
  width: 3000,
  height: 2000,
  thumb: "http://api/t.webp",
  medium: "http://api/m.webp",
  large: "http://api/l.webp",
};

describe("PublicationCard", () => {
  it("links the title and shows the date and excerpt", () => {
    render(
      <PublicationCard
        item={{
          id: 1,
          slug: "a",
          title: "Як посадити",
          published_at: "2026-11-19",
          cover: null,
          excerpt: "Коротко",
        }}
        href="/articles/a"
        locale="uk"
      />,
    );
    expect(screen.getByRole("link", { name: "Як посадити" })).toHaveAttribute(
      "href",
      "/articles/a",
    );
    expect(screen.getByText("19 листопада 2026 р.")).toHaveAttribute("datetime", "2026-11-19");
    expect(screen.getByText("Коротко")).toBeInTheDocument();
  });

  it("shows the cover when there is one", () => {
    const cover = {
      card: "http://api/c.webp",
      large: "http://api/cl.webp",
      width: 800,
      height: 450,
    };
    const { container } = render(
      <PublicationCard
        item={{ id: 1, slug: "a", title: "Новина", published_at: "2026-01-02", cover }}
        href="/news/a"
        locale="en"
      />,
    );
    expect(container.querySelector("img")).toHaveAttribute("src", "http://api/c.webp");
    expect(screen.getByText("January 2, 2026")).toBeInTheDocument();
  });
});

describe("photo album helpers", () => {
  it("fits renditions without upscaling", () => {
    expect(fitSize(3000, 2000, 1000)).toEqual({ width: 1000, height: 667 });
    expect(fitSize(300, 200, 1000)).toEqual({ width: 300, height: 200 });
  });

  it("builds a responsive album photo", () => {
    const photo = toAlbumPhoto(image, 0);
    expect(photo).toMatchObject({
      key: "7",
      src: "http://api/m.webp",
      alt: "Гроно",
      large: "http://api/l.webp",
    });
    expect(photo.srcSet?.map((item) => item.width)).toEqual([400, 1000, 1800]);
    expect(toAlbumPhoto({ ...image, width: null, height: null }, 1)).toMatchObject({
      width: 1200,
      height: 900,
    });
  });

  it("uses the source title as the alt text of feed photos", () => {
    const source = { kind: "album" as const, slug: "harvest", title: "Збір врожаю" };
    expect(feedImage({ ...image, id: "album-7", alt: "", source }).alt).toBe("Збір врожаю");
  });
});

describe("GalleryTabs", () => {
  it("marks the active tab", () => {
    render(<GalleryTabs active="all" hrefFor={(path) => `/en${path}`} t={t} />);
    expect(screen.getByRole("link", { name: "All photos" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("link", { name: "Albums" })).toHaveAttribute("href", "/en/gallery");
  });
});

describe("socialLinks", () => {
  it("lists only filled links", () => {
    const links = socialLinks(
      {
        facebook: "",
        instagram: "https://i.example",
        youtube: "",
        telegram: "",
        forum: "https://f.example",
      },
      { t },
    );
    expect(links).toEqual([
      { href: "https://i.example", label: "Instagram" },
      { href: "https://f.example", label: "Forum" },
    ]);
  });
});

describe("RichText", () => {
  it("renders sanitized HTML from the API, or nothing", () => {
    const { container, rerender } = render(<RichText html="<p>Текст</p>" />);
    expect(container.querySelector("p")).toHaveTextContent("Текст");
    rerender(<RichText html="" />);
    expect(container).toBeEmptyDOMElement();
  });
});
