import Link from "next/link";

import { cn } from "@/lib/utils";

/**
 * Alphabet navigation. Letters without published varieties are muted and not links
 * (when `available` is null, e.g. the API is down, every letter stays a link).
 */
export function AlphabetBar({
  letters,
  available,
  active,
  hrefFor,
  label,
  className,
}: {
  letters: string[];
  available: string[] | null;
  active?: string;
  hrefFor: (letter: string) => string;
  label: string;
  className?: string;
}) {
  const enabled = available ? new Set(available) : null;

  return (
    <nav aria-label={label} className={className}>
      <ul className="flex flex-wrap justify-center gap-x-0.5 gap-y-1">
        {letters.map((letter) => {
          const base =
            "inline-flex h-7 min-w-7 items-center justify-center rounded px-1.5 text-sm font-medium";
          if (letter === active) {
            return (
              <li key={letter}>
                <Link
                  href={hrefFor(letter)}
                  aria-current="true"
                  className={cn(base, "bg-primary text-primary-foreground")}
                >
                  {letter}
                </Link>
              </li>
            );
          }
          if (enabled && !enabled.has(letter)) {
            return (
              <li key={letter}>
                <span aria-disabled="true" className={cn(base, "text-muted-foreground/40")}>
                  {letter}
                </span>
              </li>
            );
          }
          return (
            <li key={letter}>
              <Link
                href={hrefFor(letter)}
                className={cn(base, "text-muted-foreground hover:bg-muted hover:text-primary")}
              >
                {letter}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
