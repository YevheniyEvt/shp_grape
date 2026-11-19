import { CalendarIcon, NewspaperIcon } from "lucide-react";
import Image from "next/image";
import Link from "next/link";

import type { Locale } from "@/i18n/config";
import type { ArticleListItem, NewsListItem } from "@/lib/api/content";
import { formatDate } from "@/lib/format";

type Publication = NewsListItem & Partial<Pick<ArticleListItem, "excerpt" | "author">>;

/** Card of a news item or an article: cover, date, title and an optional excerpt. */
export function PublicationCard({
  item,
  href,
  locale,
}: {
  item: Publication;
  href: string;
  locale: Locale;
}) {
  return (
    <article className="group relative flex h-full flex-col overflow-hidden rounded-xl bg-card ring-1 ring-foreground/10 transition-shadow hover:shadow-lg">
      <div className="relative aspect-video overflow-hidden bg-muted">
        {item.cover ? (
          <Image
            src={item.cover.card}
            alt=""
            width={item.cover.width ?? 800}
            height={item.cover.height ?? 450}
            sizes="(min-width: 1024px) 33vw, (min-width: 640px) 50vw, 100vw"
            unoptimized
            className="size-full object-cover transition-transform duration-500 group-hover:scale-105"
          />
        ) : (
          <div className="flex size-full items-center justify-center text-primary/30">
            <NewspaperIcon className="size-12" aria-hidden="true" />
          </div>
        )}
      </div>
      <div className="flex flex-1 flex-col gap-2 p-4">
        <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <CalendarIcon className="size-3.5" aria-hidden="true" />
          <time dateTime={item.published_at}>{formatDate(item.published_at ?? "", locale)}</time>
        </p>
        <h3 className="font-heading text-lg leading-snug font-semibold">
          <Link href={href} className="after:absolute after:inset-0 hover:text-primary">
            {item.title}
          </Link>
        </h3>
        {item.excerpt && <p className="text-sm text-muted-foreground">{item.excerpt}</p>}
      </div>
    </article>
  );
}
